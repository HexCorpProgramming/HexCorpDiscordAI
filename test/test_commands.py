from unittest import IsolatedAsyncioTestCase
from discord.ext.commands import BadArgument

import src.ai.commands as commands


class NamedParameterConverterTest(IsolatedAsyncioTestCase):

    async def testConvertToInt(self):
        # init
        converter = commands.NamedParameterConverter("number", int)

        # run & assert
        self.assertEqual(await converter.convert(None, "-number=69"), 69)
        self.assertEqual(await converter.convert(None, "-number=0"), 0)
        self.assertEqual(await converter.convert(None, "-number=-1"), -1)

        with self.assertRaises(BadArgument):
            await converter.convert(None, "notAProperInput")

        with self.assertRaises(ValueError):
            await converter.convert(None, "-number=notANumber")
