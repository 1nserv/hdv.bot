import dotenv, os
from nsarchive.tools import setup
import nsarchive as nsa

dotenv.load_dotenv(override = True)
setup(os.getenv("PATH"))

entities = nsa.EntityInterface(os.getenv("PATH"))

full_perms = nsa.PositionPermissions()
for p in full_perms.__dict__.keys():
    setattr(full_perms, p, True)

# ============ GRADES ============

citizen = entities.create_position(
    'citizen',
    'Citoyen',
    nsa.PositionPermissions([
        'create_groups',
        'create_parties',
        'vote'
    ]),
    entities.get_position('membre'),
    1
)


servant = entities.create_position(
    'servant',
    'Fonctionnaire',
    nsa.PositionPermissions([
        'investigate' # Temporaire
    ]),
    citizen,
    2
)


officer = entities.create_position(
    'officer',
    'Officier',
    nsa.PositionPermissions([
        'investigate', # Temporaire
    ]),
    citizen,
    3
)

police = entities.create_position(
    'police',
    'Modérateur',
    nsa.PositionPermissions([
        'handle_reports',
        'manage_lawsuits',
        'moderate_entities',
        'moderate_groups'
    ]),
    officer,
    1
)


state_officer = entities.create_position(
    'state_officer',
    'Officier d\'État',
    nsa.PositionPermissions([
        'investigate',
    ]),
    officer,
    2
)

repr = entities.create_position(
    'repr',
    'Député',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate',
        'moderate_groups',
        'vote_laws'
    ]),
    officer,
    2
)

judge = entities.create_position(
    'judge',
    'Juge',
    nsa.PositionPermissions([
        'investigate',
        'manage_lawsuits',
        'moderate_entities',
        'moderate_groups'
    ]),
    officer,
    2
)


gd_state_offi = entities.create_position(
    'gd_state_officer',
    'Grand Officier d\'État',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate'
    ]),
    officer,
    3
)

minister = entities.create_position(
    'minister',
    'Ministre',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate',
        'manage_bots',
        'manage_certifications',
        'manage_officers',
        'manage_positions'
    ]),
    officer,
    3
)

pre_an = entities.create_position(
    'assembly_president',
    'Président de l\'Assemblée Nationale',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate',
        'moderate_groups',
        'vote_laws'
    ]),
    officer,
    3
)


garant = entities.create_position(
    'garant',
    'Garant',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate',
        'manage_bots',
        'manage_certifications',
        'manage_government',
        'manage_positions'
    ]),
    officer,
    4
)

garant = entities.create_position(
    'president',
    'Président de la République',
    nsa.PositionPermissions([
        'edit_laws',
        'investigate',
        'manage_bots',
        'manage_certifications',
        'manage_government',
        'manage_positions'
    ]),
    officer,
    4
)

garant = entities.create_position(
    'sage',
    'Sage',
    nsa.PositionPermissions([
        'investigate',
        'manage_bots',
        'manage_certifications',
        'manage_elections',
        'manage_government',
        'manage_positions'
    ]),
    officer,
    5
)


admin = entities.create_position(
    'admin',
    'Administrateur',
    full_perms,
    officer,
    6
)

entities.create_position(
    'parti',
    'Parti politique',
    nsa.PositionPermissions(),
    entities.get_position('group'),
    1
)


# ============= ADMINS ============

usr = entities.create_user(
    id = nsa.NSID(1116248453127876618),
    name = 'happex',
    position = admin.id
)

usr = entities.create_user(
    id = nsa.NSID(855440355686875216),
    name = 'Kheops',
    position = admin.id
)

usr = entities.create_user(
    id = nsa.NSID(810837191587790849),
    name = 'Akel',
    position = admin.id
)

usr = entities.create_user(
    id = nsa.NSID(848242824906276894),
    name = 'Alexis',
    position = admin.id
)