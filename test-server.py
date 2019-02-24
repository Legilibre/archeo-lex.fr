import unittest

import collections

from server import get_summary

class ServerTest(unittest.TestCase):

    def test_get_summary(self):

        text = """# Title 1

## Subtitle 11

### Article 11-1

Habeas corpus 11-1.

Habeas rosam 11-1.

# Title 2

## Subtitle 21

### Subsubtitle 211

#### Article 211-1

Habeas corpus 211-1.

Habeas rosam 211-1.

#### Article 211-2

Habeas corpus 211-2.

Habeas rosam 211-1.
"""

        summary = collections.OrderedDict()
        summary['Title 1'] = collections.OrderedDict()
        summary['Title 1']['Subtitle 11'] = collections.OrderedDict({'Article 11-1': None})
        summary['Title 2'] = collections.OrderedDict()
        summary['Title 2']['Subtitle 21'] = collections.OrderedDict()
        summary['Title 2']['Subtitle 21']['Subsubtitle 211'] = collections.OrderedDict({'Article 211-1': None})
        summary['Title 2']['Subtitle 21']['Subsubtitle 211']['Article 211-2'] = None

        articles = collections.OrderedDict()
        articles['11-1'] = ['Title 1', 'Subtitle 11']
        articles['211-1'] = ['Title 2', 'Subtitle 21', 'Subsubtitle 211']
        articles['211-2'] = ['Title 2', 'Subtitle 21', 'Subsubtitle 211']

        self.assertEqual(get_summary(text), (summary, articles))


if __name__ == '__main__':

    unittest.main()

# vim: set ts=4 sw=4 sts=4 et:
