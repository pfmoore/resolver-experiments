from pprint import pprint
from resolvelib import Resolver, BaseReporter, AbstractProvider
from packaging.version import Version
from packaging.requirements import Requirement
from yaml import safe_load

def trace(f):
    def wrapper(*args, **kw):
        print("Calling", f.__name__)
        pprint(args)
        pprint(kw)
        ret = f(*args, **kw)
        print("Returned:")
        pprint(ret)
        return ret
    return wrapper

class Reporter(BaseReporter):
    def starting(self):
        pass
    def starting_round(self, index):
        print(f"********** STARTING ROUND {index}")
    def ending_round(self, index, state):
        pass
    def ending(self, state):
        pass

from collections import namedtuple
Candidate = namedtuple('Candidate', 'name version')

class Provider(AbstractProvider):
    def __init__(self, data):
        self.data = data
        self.candidates = []
        self.dependencies = {}
        for c in self.data['Candidates']:
            name, version = c.split()
            version = Version(version)
            self.candidates.append(Candidate(name, version))
        pprint(self.candidates)
        for c, d in self.data['Dependencies'].items():
            name, _, version = c.partition(' ')
            if version:
                version = Version(version)
                self.dependencies[Candidate(name, version)] = [Requirement(d)]
            else:
                self.dependencies[name] = Requirement(d)
        pprint(self.dependencies)
    def identify(self, dependency):
        return dependency.name
    def get_preference(self, resolution, candidates, information):
        return len(candidates)
    @trace
    def find_matches(self, requirement):
        candidates = []
        for c in self.candidates:
            if c.name == requirement.name and c.version in requirement.specifier:
                candidates.append(c)
        return candidates
    @trace
    def is_satisfied_by(self, requirement, candidate):
        if requirement.name != candidate.name:
            return False
        return candidate.version in requirement.specifier
    @trace
    def get_dependencies(self, candidate):
        if candidate in self.dependencies:
            return self.dependencies[candidate]
        elif candidate.name in self.dependencies:
            return self.dependencies[candidate.name]
        else:
            return []

def display_resolution(result):

    print("--- Pinned Candidates ---")
    for name, candidate in result.mapping.items():
        print(f"{name}: {candidate.name} {candidate.version}")

    print()
    print("--- Dependency Graph ---")
    for name in result.graph:
        targets = ", ".join(result.graph.iter_children(name))
        print(f"{name} -> {targets}")

def main(data, reqs):
    # Things I want to resolve.
    requirements = [Requirement(r) for r in reqs]

    provider = Provider(data)
    reporter = Reporter()

    # Create the (reusable) resolver.
    resolver = Resolver(provider, reporter)

    # Kick off the resolution process, and get the final result.
    result = resolver.resolve(requirements)
    
    display_resolution(result)

if __name__ == "__main__":
    import sys
    from pathlib import Path
    data = safe_load(Path(sys.argv[1]).read_text())
    pprint(data)
    main(data, sys.argv[2:])

