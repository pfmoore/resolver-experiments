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
        print("Starting")
    def starting_round(self, index):
        print("Starting round")
    def ending_round(self, index, state):
        print("Ending round")
    def ending(self, state):
        print("Ending")

class Provider(AbstractProvider):
    def identify(self, dependency):
        print(f"identify({dependency})")
        return dependency.name
    def get_preference(self, resolution, candidates, information):
        print(f"get_preference()")
        # Need to work out what this is for!
        return len(candidates)
    def find_matches(self, requirement):
        print(f"find_matches({requirement})")
        candidates = []
        for c in get(requirement.name):
            version = str(c.version)
            #print(f"Checking {c.name}:{version}")
            if version in requirement.specifier and c.filetype == "wheel":
                candidates.append(c)
        return candidates
    def is_satisfied_by(self, requirement, candidate):
        print(f"is_satisfied_by({requirement}, {candidate})")
        if requirement.name != candidate.name:
            return False
        return candidate.version in requirement.specifier
    def get_dependencies(self, candidate):
        print(f"get_dependencies({candidate})")
        return candidate.dependencies()

# Things I want to resolve.
requirements = [Requirement("requests")]

provider = Provider()
reporter = Reporter()

# Create the (reusable) resolver.
resolver = Resolver(provider, reporter)

# Kick off the resolution process, and get the final result.
result = resolver.resolve(requirements)
for project, c in result.mapping.items():
    print(project, c.name, c.version)

print(result)
