import dotenv, os
from nsarchive.tools import setup
import nsarchive as nsa

dotenv.load_dotenv(override = True)
setup(os.getenv("PATH"))

entities = nsa.EntityInterface(os.getenv("PATH"))

perms = nsa.PositionPermissions()
for p in perms.__dict__.keys():
    setattr(perms, p, True)

position = entities.create_position(
    'admin',
    'Administrateur',
    perms,
    entities.get_position('membre')
)

entities.create_position(
    'parti',
    'Parti politique',
    nsa.PositionPermissions(),
    entities.get_position('group')
)

usr = entities.create_user(
    id = nsa.NSID(1116248453127876618),
    name = 'happex',
    position = position.id
)

print(usr._to_dict())

usr = entities.create_user(
    id = nsa.NSID(855440355686875216),
    name = 'Kheops',
    position = position.id
)

print(usr._to_dict())

usr = entities.create_user(
    id = nsa.NSID(810837191587790849),
    name = 'Akel',
    position = position.id
)

print(usr._to_dict())

usr = entities.create_user(
    id = nsa.NSID(848242824906276894),
    name = 'Alexis',
    position = position.id
)

print(usr._to_dict())