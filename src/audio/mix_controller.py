"""
####### mix_controller.py #######

### Auth: MoncherBen, Oct. 2026
"""


def calculate_tempo_ratio(source_bpm: float, target_bpm: float) -> float:
    """ Typically.

        source_bpm (float): the bpm of the former track
        target_bpm (float): the bpm of the later track
        
        -> (float): the ratio
    """
    if source_bpm <= 0 or target_bpm <= 0:
        raise ValueError("Les BPM doivent être strictement positifs.")

    return target_bpm / source_bpm


def calculate_tempo_change(source_bpm: float, target_bpm: float) -> float:
    """ Tempo variation in percent.

        source_bpm (float): the bpm of the former track
        target_bpm (float): the bpm of the later track
        
        -> (float): the variation percentage
    """
    ratio = calculate_tempo_ratio(source_bpm, target_bpm)
    return (ratio - 1.0) * 100.0


def calculate_average_bpm(bpm_a: float, bpm_b: float) -> float:
    """ Typically.

        bpm_a (float): the bpm of the former track
        bpm_b (float): the bpm of the later track
        
        -> (float): the average bpm
    """
    if bpm_a <= 0 or bpm_b <= 0:
        raise ValueError("Les BPM doivent être strictement positifs.")

    return (bpm_a + bpm_b) / 2.0


def is_within_recommended_range(source_bpm: float,
                                target_bpm: float,
                                tolerance: float = 0.1) -> bool:
    """Check if variation stays in a recommanded limit.

        source_bpm (float): the bpm of the former track
        target_bpm (float): the bpm of the later track
        tolerance (float): the recommanded tolerance

        -> (bool)
    """
    ratio = calculate_tempo_ratio(source_bpm, target_bpm)
    return 1.0 - tolerance <= ratio <= 1.0 + tolerance
