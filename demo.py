from resolvelib import Resolver, BaseReporter, AbstractProvider
from packaging import version as v, specifiers as s
from index import get, Requirement


#class Candidate:
#    def __init__(self, name, version):
#        self.name = name
#        self.version = v.parse(version)

#class Requirement:
#    def __init__(self, name, spec):
#        self.name = name
#        self.spec = s.SpecifierSet(spec)

class Reporter(BaseReporter):
    def starting(self):
        #print("Starting")
        pass
    def starting_round(self, index):
        #print("Starting round")
        pass
    def ending_round(self, index, state):
        #print("Ending round")
        pass
    def ending(self, state):
        #print("Ending")
        pass

class Provider(AbstractProvider):
    def identify(self, dependency):
        return dependency.name
    def get_preference(self, resolution, candidates, information):
        return len(candidates)
    def find_matches(self, requirement):
        candidates = []
        for c in get(requirement.name, requirement.extras):
            version = str(c.version)
            if version in requirement.specifier and c.filetype == "wheel":
                candidates.append(c)
        return candidates
    def is_satisfied_by(self, requirement, candidate):
        if requirement.name != candidate.name:
            return False
        return candidate.version in requirement.specifier
    def get_dependencies(self, candidate):
        return list(candidate.dependencies())

def display_resolution(result):

    print("--- Pinned Candidates ---")
    for name, candidate in result.mapping.items():
        print(f"{name}: {candidate.name} {candidate.version}")

    print()
    print("--- Dependency Graph ---")
    for name in result.graph:
        targets = ", ".join(result.graph.iter_children(name))
        print(f"{name} -> {targets}")

def main(reqs):
    # Things I want to resolve.
    requirements = [Requirement(r) for r in reqs]

    provider = Provider()
    reporter = Reporter()

    # Create the (reusable) resolver.
    resolver = Resolver(provider, reporter)

    # Kick off the resolution process, and get the final result.
    result = resolver.resolve(requirements)

    display_resolution(result)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
