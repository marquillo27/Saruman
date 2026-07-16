TILE_SIZE = 16
SCALE = 3
INTERNAL_W = 320
INTERNAL_H = 180
WINDOW_W = INTERNAL_W * SCALE   # 960
WINDOW_H = INTERNAL_H * SCALE   # 540
FPS = 60

GRAVITY = 0.45
JUMP_VEL = -9.0
MAX_FALL_SPEED = 14.0
MOVE_SPEED = 2.5
COYOTE_FRAMES = 6
JUMP_BUFFER_FRAMES = 6

PLAYER_LIVES = 3
MAX_LIVES = 7    # Hearts stack up to this; starting lives stay PLAYER_LIVES
TOP_SCORES = 10

# --- Bonus power-ups ---
BONUS_SHIELD_FRAMES = 600   # 10 s of invulnerability @60fps
BONUS_FRUIT_FRAMES  = 600   # 10 s of enemies-as-fruit @60fps
BONUS_SPAWN_MIN     = 2400  # ~40 s — min frames between random bonus spawns
BONUS_SPAWN_MAX     = 4200  # ~70 s — max frames between random bonus spawns

GOBLIN_SPEED   = 0.8
WRAITH_SPEED   = 0.5
SHOOT_COOLDOWN = 20   # frames between shots
SWING_COOLDOWN = 15   # frames between melee swings (faster than ranged)
SHIELD_CD      = 45   # frames of shield lockout after absorbing a hit (~0.75 s)
HIT_IFRAMES    = 60   # invincibility frames after damage
STOMP_BOUNCE   = -5.0 # upward vel after a stomp kill

# --- Enemy tuning ---
BOSS_SPEED          = 1.4
BOSS_CHARGE_R       = 110  # pixel radius within which a boss charges the player

# Animation rate = ticks per sprite frame (higher = slower cycle)
GOBLIN_ANIM_RATE       = 6
WRAITH_ANIM_RATE       = 10
BOSSWARG_ANIM_RATE     = 8
SHIELDKNIGHT_ANIM_RATE = 8
ARCHER_ANIM_RATE       = 8
BAT_ANIM_RATE          = 6
SLIME_ANIM_RATE        = 6
SMALL_SLIME_ANIM_RATE  = 6
SPITTER_ANIM_RATE      = 12
MIMIC_ANIM_RATE        = 6
GOBLINKING_ANIM_RATE   = 8
NIGHTKING_ANIM_RATE    = 8

# Floating-bob amplitude (pixels)
WRAITH_FLOAT_AMP = 3.0
BAT_FLOAT_AMP    = 2.5

# GoblinKing per-phase charge speed
GOBLINKING_SPEED_P1 = 1.8
GOBLINKING_SPEED_P2 = 2.8

# Night King (final boss) per-phase charge speed
NIGHTKING_SPEED_P1 = 1.5
NIGHTKING_SPEED_P2 = 2.6

TITLE = "Project Saruman"

# Wolfwood twilight palette
COL_SKY_TOP    = (15,  20,  45)
COL_SKY_BOT    = (35,  45,  80)
COL_FOG        = (60,  70, 100, 90)   # RGBA
COL_UI_BG      = (10,  10,  20, 200)
COL_WHITE      = (240, 240, 240)
COL_GOLD       = (212, 161,  85)
COL_RED        = (200,  50,  50)
COL_GREEN      = ( 80, 180,  80)
COL_DARK_GRAY  = ( 40,  40,  50)
