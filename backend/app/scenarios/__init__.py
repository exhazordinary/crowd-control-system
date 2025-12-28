from .bukit_jalil_exit import BUKIT_JALIL_EXIT_SCENARIO
from .axiata_concert import AXIATA_CONCERT_SCENARIO
from .pavilion_festival import PAVILION_FESTIVAL_SCENARIO

SCENARIOS = {
    "bukit-jalil-exit": BUKIT_JALIL_EXIT_SCENARIO,
    "axiata-concert": AXIATA_CONCERT_SCENARIO,
    "pavilion-festival": PAVILION_FESTIVAL_SCENARIO,
}

__all__ = [
    "BUKIT_JALIL_EXIT_SCENARIO",
    "AXIATA_CONCERT_SCENARIO",
    "PAVILION_FESTIVAL_SCENARIO",
    "SCENARIOS"
]
