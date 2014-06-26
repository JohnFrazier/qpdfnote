class Citation():
    def __init__(self, name="", path=""):
        self.name = name
        self.path = path
        self.refs = [] # (page, line)
        self.pageRefPat = None # = re.compile(":digit:*")#(\::digit:*")
        self.mdappendix = "[{name}:]{path} {year}, {pages}"

    def addRef(self, ref):
        if type(ref) == type(tuple):
            self.refs.append(ref)
            return 0
        return 1

    def asMD(self):
        return self.mdappendix.format(self.name, self.path, self._refPages())

    def _refPages(self):
        return ", ".join(["{p}:{l}".format(p, l) for p, l in self.refs])

    def setCSLjson(self, csl):
        pass

    def asCSLjson(self):
        pass
