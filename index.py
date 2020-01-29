import requests
import html5lib
from urllib.parse import urlparse
from packaging.markers import Marker
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from packaging.requirements import Requirement # Suitable for resolvelib
import sys
from io import BytesIO
from zipfile import ZipFile
from email.parser import BytesParser

class Candidate:
    def __init__(self, url):
        self.url = url
        path = urlparse(url).path
        self.filename = path.rpartition('/')[-1]
        self.filetype, self.name, self.version = parse(self.filename)
        if self.version:
            self.version = Version(self.version)
        self.metadata = None

    def __str__(self):
        return f"Candidate({self.name}, {self.version})"

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
            print(f"{self.name} -> {deps}")
            return [Requirement(d) for d in deps]
        return []

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

def get(name):
    url = f"https://pypi.org/simple/{name}"
    data = requests.get(url).content
    #print(data)
    doc = html5lib.parse(data, namespaceHTMLElements=False)
    for i in doc.findall(".//a"):
        c = Candidate(i.attrib["href"])
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
