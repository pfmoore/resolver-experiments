import requests
import html5lib
from urllib.parse import urlparse
from packaging.markers import Marker
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion
from packaging.requirements import Requirement # Suitable for resolvelib
import sys
from io import BytesIO
from zipfile import ZipFile
from email.parser import BytesParser

class Candidate:
    def __init__(self, url, extras=None):
        self.url = url
        path = urlparse(url).path
        self.filename = path.rpartition('/')[-1]
        self.filetype, self.name, self.version = parse(self.filename)
        if self.version:
            try:
                self.version = Version(self.version)
            except InvalidVersion:
                self.version = Version("0")
        self.metadata = None
        self.extras = extras

    def __str__(self):
        return f"Candidate({self.name}[{self.extras}], {self.version})"

    def get_metadata(self):
        if self.filetype != "wheel":
            print(f"{self.name}: No wheel fo type {self.filetype}")
            return
        if self.metadata:
            return
        data = requests.get(self.url).content
        with ZipFile(BytesIO(data)) as z:
            for n in z.namelist():
                if n.endswith('.dist-info/METADATA'):
                    p = BytesParser()
                    self.metadata = p.parse(z.open(n), headersonly=True)
                    break

    def requires_python(self):
        self.get_metadata()
        if self.metadata:
            return self.metadata.get("Requires-Python")
        return None

    def dependencies(self):
        print(f"Looking for dependencies: {self}")
        self.get_metadata()
        if self.metadata:
            deps = self.metadata.get_all("Requires-Dist", [])
            extras = self.extras if self.extras else ['']
            print(f"{self.name} -> {deps}")
            for d in deps:
                r = Requirement(d)
                if r.marker is None:
                    yield r
                else:
                    for e in extras:
                        if r.marker.evaluate({'extra': e}):
                            yield r
        # If we have extras, we also depend on the base package having
        # the same version
        if self.extras:
            yield Requirement(f"{self.name} == {self.version}")

py_ver = Version(".".join(map(str, sys.version_info[:2])))
print(py_ver)

def parse(filename):
    filetype = None
    name = None
    version = None

    if filename.endswith('.zip'):
        filetype = "sdist"
        filename = filename[:-4]
    elif filename.endswith('.tar.gz'):
        filetype = "sdist"
        filename = filename[:-7]
    elif filename.endswith('.whl'):
        filetype = "wheel"
        filename = filename[:-4]
    elif filename.endswith(('.egg', '.rpm', '.exe', '.msi')):
        return "Unknown", name, version

    if filetype == "wheel":
        name, version = filename[:-4].split('-')[:2]
    else:
        name, _, version = filename.rpartition('-')

    return filetype, name, version

def get(name, extras=None):
    url = f"https://pypi.org/simple/{name}"
    data = requests.get(url).content
    #print(data)
    doc = html5lib.parse(data, namespaceHTMLElements=False)
    for i in doc.findall(".//a"):
        c = Candidate(i.attrib["href"], extras)
        if c.version is None:
            continue
        py_req = i.attrib.get("data-requires-python")
        if py_req:
            spec = SpecifierSet(py_req)
            if py_ver not in spec:
                continue
        #TODO: Skip incompatible wheels
        yield c

def main(name):
    for c in get(name):
        print(c.filetype, c.name, c.version)

if __name__ == '__main__':
    import sys
    name = sys.argv[1]
    main(name)
