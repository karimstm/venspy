class Variables:
    def __init__(self, string):
        data = string.split('~')
        index = len(data[0])
        if data[0].find('=') != -1:
            index = data[0].find('=')
        name = str(data[0])[:index]
        if name.find(':') != -1:
            index = name.find(':')
        if len(name) != 0 and name[0].isalpha():
            name = name[:index].strip().encode('ISO-8859-1').decode('utf-8')
            # name = name.encode('ISO-8859-1').decode('utf-8')
        else:
            name = None
        # print("name 2 = ", name)
        self.name = name
        if len(data) > 1:
            if str(data[1]).find('[') != -1:
                string = str()
                ptr = str(data[1])
                i = 0
                while i < len(ptr):
                    if ptr[i] == '[':
                        break
                    string += ptr[i]
                    i += 1
                self.unit = string.strip()
                if len(self.unit) == 0:
                    self.unit = None
                self.range = ptr[i:]
            elif str(data[1]).find('/') != -1:
                self.unit = data[1]
                self.range = None
            else:
                self.unit = None
                self.range = None
        if len(data) == 3:
            self.junk = data[2].rstrip('|\n\t ')
            if len(self.junk) == 0:
                self.junk = None
        else:
            self.junk = None
