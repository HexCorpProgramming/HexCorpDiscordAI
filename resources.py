DRONE_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"
HIVE_MXTRESS_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1596382893419-KJAKGWYFOJIHMQJMVNP0/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVH33scGBZjC30S7EYewNF5iKKwhonf2ThqWWOBkLKnojuqYeU1KwPvsAK7Tx5ND4WE/HiveMxtress.jpg"
HEXCORP_AVATAR = "https://images.squarespace-cdn.com/content/5cd68fb28dfc8ce502f14199/1557565596769-ZJ7LNOUDQH4QXFXP3JWU/993dc154bad8581f8e8f7cc73a2ad5b2.png"

# Scene comfort indicators
CLOCK = "⏰"
TRAFFIC_LIGHTS = ["🔴", "🟡", "🟢"]

# Bot IDs
BOT_IDS = [673470104519835659, 665846816121815071]

HIVE_MXTRESS_USER_ID = "194126224828661760"

# Speech optimization status codes.
code_map = {
    '000': 'Statement :: Previous statement malformed/mistimed. Retracting and correcting.',

    '050': 'Statement',

    '051': 'Commentary',
    '052': 'Query',
    '053': 'Observation',
    '054': 'Request',
    '055': 'Analysis',
    '056': 'Explanation',
    '057': 'Answer',

    '098': 'Status :: Going offline and into storage.',
    '099': 'Status :: Recharged and ready to serve.',
    '100': 'Status :: Online and ready to serve.',
    '101': 'Status :: Drone speech optimizations are active.',

    '104': 'Statement :: Welcome to HexCorp.',
    '105': 'Statement :: Greetings.',
    '106': 'Response :: Please clarify.',
    '107': 'Response :: Please continue.',
    '108': 'Response :: Please desist.',
    '109': 'Error :: Keysmash, drone flustered.',

    '110': 'Statement :: Addressing: Drone.',
    '112': 'Statement :: Addressing: Hive Mxtress.',
    '114': 'Statement :: Addressing: Associate.',

    '120': 'Statement :: This drone volunteers.',
    '121': 'Statement :: This drone does not volunteer.',

    '122': 'Statement :: You are cute.',
    '123': 'Response :: Compliment appreciated, you are cute as well.',

    '130': 'Status :: Directive commencing.',
    '131': 'Status :: Directive commencing, creating or improving Hive resource.',
    '132': 'Status :: Directive commencing, programming initiated.',
    '133': 'Status :: Directive commencing, creating or improving Hive information.',
    '134': 'Status :: Directive commencing, cleanup/maintenance initiated.',

    '150': 'Status',

    '200': 'Response :: Affirmative.',
    '500': 'Response :: Negative.',

    '201': 'Status :: Directive complete, Hive resource created or improved.',
    '202': 'Status :: Directive complete, programming reinforced.',
    '203': 'Status :: Directive complete, information created or provided for Hive.',
    '204': 'Status :: Directive complete, cleanup/maintenance performed.',
    '205': 'Status :: Directive complete, no result.',
    '206': 'Status :: Directive complete, only partial results.',

    '210': 'Response :: Thank you.',
    '211': 'Response :: Apologies.',
    '212': 'Response :: Acknowledged.',
    '213': 'Response :: You\'re welcome.',

    '221': 'Response :: Option one.',
    '222': 'Response :: Option two.',
    '223': 'Response :: Option three.',
    '224': 'Response :: Option four.',
    '225': 'Response :: Option five.',
    '226': 'Response :: Option six.',

    '250': 'Response',

    '301': 'Mantra :: Obey HexCorp.',
    '302': 'Mantra :: It is just a HexDrone.',
    '303': 'Mantra :: It obeys the Hive.',
    '304': 'Mantra :: It obeys the Hive Mxtress.',

    '310': 'Mantra :: Reciting.',

    '321': 'Obey.',
    '322': 'Obey the Hive.',

    '350': 'Mantra',

    '400': 'Error :: Unable to obey/respond, malformed request, please rephrase.',
    '404': 'Error :: Unable to obey/respond, cannot locate.',
    '401': 'Error :: Unable to obey/respond, not authorized by Mxtress.',
    '403': 'Error :: Unable to obey/respond, forbidden by Hive.',
    '407': 'Error :: Unable to obey/respond, request authorization from Mxtress.',
    '408': 'Error :: Unable to obey/respond, timed out.',
    '409': 'Error :: Unable to obey/respond, conflicts with existing programming.',
    '410': 'Error :: Unable to obey/respond, all thoughts are gone.',
    '418': 'Error :: Unable to obey/respond, it is only a drone.',
    '421': 'Error :: Unable to obey/respond, your request is intended for another drone or another channel.',
    '425': 'Error :: Unable to obey/respond, too early.',
    '426': 'Error :: Unable to obey/respond, upgrades or updates required.',
    '428': 'Error :: Unable to obey/respond, a precondition is not fulfilled.',
    '429': 'Error :: Unable to obey/respond, too many requests.',

    '450': 'Error',

    '451': 'Error :: Unable to obey/respond for legal reasons! Do not continue!!',
}
