PHRASES = {
    # Только на английском, Repl.it ломается на кириллице
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}

def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 25, 0.2
    elif year < 1981:
        return 19, 0.2
    elif year < 1995:
        return 15, 0.2
    elif year < 2010:
        return 13, 0.2
    elif year < 2020:
        return 11, 0.5
    else:
        return 7, 0.6
