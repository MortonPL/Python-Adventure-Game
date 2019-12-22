class ReaderTXT:

    def __init__(self, path):
        self.strlist = []
        with open(path, "r") as file:
            for line in file:
                line = line.strip('\n')
                if line == '$':
                    self.strlist.append('')
                else:
                    self.strlist.append(line)
        print(self.strlist)

    def __iter__(self):
        return IteratorReaderTXT(self)


class IteratorReaderTXT:

    def __init__(self, reference):
        self.reference = reference
        self.index = 0

    def __next__(self):
        if self.index < len(self.reference.strlist):
            result = self.reference.strlist[self.index]
            self.index += 1
            return result
        raise StopIteration
