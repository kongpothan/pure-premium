import openpyxl
import unidecode

variables_ok = set()
variables_ko = set()
variables_not_found = set()


def normalize_string(s):
    return unidecode.unidecode(str(s).upper())


class Feature():

    def __init__(self, data, i):
        self.name = data[3][i]
        self.label = data[5][i]
        self.values = self.get_values(data, i)

    def get_values(self, data, i):
        values = {}
        for j in range(6, len(data)):
            if data[j][i] is None:
                break
            modality = str(data[j][i])
            modality = normalize_string(modality)
            coefficient = float(data[j][i + 1])
            values[modality] = coefficient
        return values

    def __str__(self):
        values = [k + ' -> ' + str(v) for k, v in self.values.items()]
        return '\t' + str(self.name) + ' : ' + str(self.label) + '\n\t\t' \
            + '\n\t\t'.join(values) \
            + '\n'


class Model():

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.base = self.get_base()
        self.features = self.get_features()

    def get_base(self):
        if self.data[1][1] != 'Base':
            raise Exception("Base coefficient not found in model !", self.name)
        return float(self.data[1][2])

    def get_features(self):
        features = {}
        for i in range(len(self.data[3])):
            name = self.data[3][i]
            if name is not None:
                features[name] = Feature(self.data, i)
        return features

    def calculate(self, contract, debug=False):
        result = self.base
        for feature in self.features.values():
            value = None
            try:
                value = contract[feature.name]
            except Exception:
                if debug:
                    global variables_not_found
                    variables_not_found.add(feature.name)
                    print(self.name, ": exception", feature.name,
                          'not in data file')
                    continue
            coefficient = feature.values.get(normalize_string(value), None)
            if coefficient is not None:
                result *= coefficient
                if debug:
                    global variables_ok
                    variables_ok.add(feature.name)
                    print(self.name, ":", feature.name + ',', value,
                          "->", coefficient)
            else:
                if debug:
                    global variables_ko
                    variables_ko.add(feature.name)
                    print(self.name, ": exception ", feature.name,
                          "as", value, 'not in',
                          list(feature.values)[:4], '...')
        return result

    def __str__(self):
        return 'Model : ' + self.name + '\n' \
            + 'Base : ' + str(self.base) + '\n' \
            + 'Features : \n' \
            + '\n'.join(map(str, self.features.values())) + '\n'


class ContractIdModel(Model):

    def __init__(self):
        pass

    def calculate(self, contract, debug=False):
        return contract['NUMCNT']


class Models():

    def __init__(self, filename):
        self.models = {
            'NUMCNT': ContractIdModel()
        }
        workbook = openpyxl.load_workbook(filename=filename)
        for sheet in workbook.worksheets:
            name = sheet.title
            data = list(sheet.values)
            model = Model(name, data)
            self.models[name] = model

    def __str__(self):
        sb = []
        for name, model in self.models.items():
            sb.append(str(model))
        return '\n'.join(sb)
