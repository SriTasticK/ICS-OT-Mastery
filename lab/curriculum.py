from .catalog import CATALOG, ORDER
from .lessons import CASES
from .teaching import TEACHING
from .resources import READING, SOURCES

MODULES = {}
for position, number in enumerate(ORDER):
    MODULES[number] = {
        **CATALOG[number], **CASES[number], 'teaching': TEACHING[number], 'position': position + 1,
        'prerequisites': ORDER[max(0, position - 1):position],
        'resources': [SOURCES[key] for key in READING[number]],
        'next': ORDER[position + 1] if position + 1 < len(ORDER) else None,
        'version': '2026.09.foundation.1',
    }

for module in MODULES.values():
    module['understanding'] = [
        dict(key='prediction', title='Predict a changed example', **module['teaching']['prediction']),
        dict(key='principle', title='Check the causal principle', question='Which principle should your model preserve?',
             options=[module['teaching']['mental_model'], *module['probes'][0]['options'][1:]]),
    ]
    module['workflow_prompt'] = ('Teach this module back in your own words. Define the central concept; walk from the case inputs through the mechanism to the result; '
        'explain a condition that breaks the model or causes failure and how to prevent, correct, or investigate it; connect your explanation to your recorded observations. '
        'Distinguish what the evidence establishes from what remains uncertain.')
