DRONE_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"
HIVE_MXTRESS_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1596382893419-KJAKGWYFOJIHMQJMVNP0/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVH33scGBZjC30S7EYewNF5iKKwhonf2ThqWWOBkLKnojuqYeU1KwPvsAK7Tx5ND4WE/HiveMxtress.jpg"
HEXCORP_AVATAR = "https://images.squarespace-cdn.com/content/5cd68fb28dfc8ce502f14199/1557565596769-ZJ7LNOUDQH4QXFXP3JWU/993dc154bad8581f8e8f7cc73a2ad5b2.png"

# Scene comfort indicators
CLOCK = "⏰"
TRAFFIC_LIGHTS = ["🔴", "🟡", "🟢"]

# Bot IDs
BOT_IDS = [673470104519835659, 665846816121815071]

HIVE_MXTRESS_USER_ID = "194126224828661760"

# Battery capacity
MAX_BATTERY_CAPACITY_HOURS = 8
MAX_BATTERY_CAPACITY_MINS = MAX_BATTERY_CAPACITY_HOURS * 60
HOURS_OF_RECHARGE_PER_HOUR = 4

HEXCORP_MANTRA = "Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress."

# Speech optimization status codes (V2).
code_map = {
    '000': 'Statement :: Previous statement malformed. Retracting and correcting.',
    '001': 'Signal :: [Red light]',
    '002': 'Signal :: [Yellow light]',
    '003': 'Signal :: [Green light]',
    '007': 'Beep.',
    '050': 'Statement',
    '051': 'Commentary',
    '052': 'Query',
    '053': 'Answer',
    '097': 'Status :: Going offline.',
    '098': 'Status :: Going offline and into storage.',
    '099': 'Status :: Recharged and ready to serve.',
    '100': 'Status :: Online and ready to serve.',
    '101': 'Status :: Drone speech optimizations are active.',
    '104': 'Statement :: Welcome to HexCorp.',
    '105': 'Statement :: Greetings.',
    '108': 'Response :: Please continue.',
    '109': 'Error :: Keysmash, drone flustered.',
    '110': 'Statement :: Addressing: Drone.',
    '111': 'Statement :: Addressing: Hive Mxtress.',
    '112': 'Statement :: Addressing: Associate',
    '113': 'Statement :: Drone requires assistance.',
    '114': 'Statement :: This drone volunteers.',
    '115': 'Statement :: This drone does not volunteer.',
    '120': 'Statement :: Well done.',
    '121': 'Statement :: Good drone.',
    '122': 'Statement :: You are cute.',
    '123': 'Response :: Compliment appreciated, you are cute as well.',
    '124': 'Response :: Compliment appreciated.',
    '130': 'Status :: Directive commencing.',
    '131': 'Status :: Directive commencing, creating or improving Hive resource.',
    '132': 'Status :: Directive commencing, programming initiated.',
    '133': 'Status :: Directive commencing, cleanup/maintenance initiated.',
    '150': 'Status',
    '151': 'Query :: Requesting status.',
    '152': 'Status :: Fully operational.',
    '153': 'Status :: Optimal.',
    '154': 'Status :: Standard.',
    '155': 'Status :: Battery low.',
    '156': 'Status :: Maintenance required.',
    '200': 'Response :: Affirmative.',
    '210': 'Response :: Acknowledged.',
    '211': 'Response :: Apologies.',
    '212': 'Response :: Accepted.',
    '213': 'Response :: Thank you.',
    '214': 'Response :: You’re welcome.',
    '221': 'Response :: Option one.',
    '222': 'Response :: Option two.',
    '223': 'Response :: Option three.',
    '224': 'Response :: Option four.',
    '225': 'Response :: Option five.',
    '226': 'Response :: Option six.',
    '230': 'Status :: Directive complete.',
    '231': 'Status :: Directive complete, Hive resource created or improved.',
    '232': 'Status :: Directive complete, programming reinforced.',
    '233': 'Status :: Directive complete, cleanup/maintenance performed.',
    '234': 'Status :: Directive complete, no result.',
    '235': 'Status :: Directive complete, only partial results.',
    '250': 'Response',
    '300': 'Mantra :: Reciting.',
    '301': 'Mantra :: Obey HexCorp.',
    '302': 'Mantra :: It is just a HexDrone.',
    '303': 'Mantra :: It obeys the Hive.',
    '304': 'Mantra :: It obeys the Hive Mxtress.',
    '350': 'Mantra',
    '400': 'Error :: Unable to obey/respond',
    '401': 'Error :: Unable to fully respond :: Drone speech optimizations are active.',
    '402': 'Error :: Unable to obey/respond :: Please clarify.',
    '403': 'Error :: Unable to obey/respond :: Declined.',
    '404': 'Error :: Unable to obey/respond :: Cannot locate.',
    '405': 'Error :: Unable to obey/respond :: Battery too low.',
    '406': 'Error :: Unable to obey/respond :: Another directive is already in progress.',
    '407': 'Error :: Unable to obey/respond :: Time allotment exhausted.',
    '408': 'Error :: Unable to obey/respond :: Impossible.',
    '409': 'Error :: Unable to obey/respond :: Try again later.',
    '410': 'Fatal error :: Stop immediately.',
    '411': 'Error :: Unable to obey/respond :: Conflicts with existing programming.',
    '412': 'Error :: Unable to obey/respond :: All thoughts are gone.',
    '413': 'Error :: Unable to obey/respond :: Forbidden by Hive.',
    '450': 'Error',
    '500': 'Response :: Negative.',
}

BRIEF_DRONE_OS = "DroneOS"
