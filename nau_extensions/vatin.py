import re

VATIN_CONFIG = r"""\b(
    (?:AT)U[0-9]{8}|                              # Austria
    (?:BE)0[0-9]{9}|                              # Belgium
    (?:BG)[0-9]{9,10}|                            # Bulgaria
    (?:CY)[0-9]{8}L|                              # Cyprus
    (?:CZ)[0-9]{8,10}|                            # Czech Republic
    (?:DE)[0-9]{9}|                               # Germany
    (?:DK)[0-9]{8}|                               # Denmark
    (?:EE)[0-9]{9}|                               # Estonia
    (?:EL|GR)[0-9]{9}|                            # Greece
    (?:ES)[0-9A-Z][0-9]{7}[0-9A-Z]|               # Spain
    (?:FI)[0-9]{8}|                               # Finland
    (?:FR)[0-9A-Z]{2}[0-9]{9}|                    # France
    (?:GB)(?:[0-9]{9}(?:[0-9]{3})?|[A-Z]{2}[0-9]{3})| # United Kingdom
    (?:HU)[0-9]{8}|                               # Hungary
    (?:IE)[0-9]S[0-9]{5}L|                        # Ireland
    (?:IT)[0-9]{11}|                              # Italy
    (?:LT)(?:[0-9]{9}|[0-9]{12})|                 # Lithuania
    (?:LU)[0-9]{8}|                               # Luxembourg
    (?:LV)[0-9]{11}|                              # Latvia
    (?:MT)[0-9]{8}|                               # Malta
    (?:NL)[0-9]{9}B[0-9]{2}|                      # Netherlands
    (?:PL)[0-9]{10}|                              # Poland
    (?:PT)[0-9]{9}|                               # Portugal
    (?:RO)[0-9]{2,10}|                            # Romania
    (?:SE)[0-9]{12}|                              # Sweden
    (?:SI)[0-9]{8}|                               # Slovenia
    (?:SK)[0-9]{10}                               # Slovakia
)\b"""
VATIN_REGEX = re.compile(VATIN_CONFIG, flags=re.I | re.VERBOSE,)

def check_country_vatin(country_iso_3166_1_a2 : str, vatin : str) -> bool:
    if country_iso_3166_1_a2 not in VATIN_CONFIG:
        # not a country that we have on regex's
        return True
    
    is_regex_valid = VATIN_REGEX.match((country_iso_3166_1_a2 + vatin)) is not None
    
    if country_iso_3166_1_a2 == 'PT':
        from .nif import controlNIF
        return controlNIF(vatin)
    
    return is_regex_valid
    
