from bs4 import BeautifulSoup
from collections import defaultdict, namedtuple
from functools import reduce
'''
data from https://www.footballdb.com/games/index.html
'''
Team = namedtuple('Team', 'abbreviation conference division'.split())
Record = namedtuple('Record', 'wins losses ties'.split()) 
ConferenceRecord = namedtuple('ConferenceRecord', 'wins losses ties'.split()) 
DivisionRecord = namedtuple('DivisionRecord', 'wins losses ties'.split()) 
Game = namedtuple('Game', 'date where opponent conference division result scored allowed'.split())
VictoryStrength = namedtuple('VictoryStrength', 'wins losses ties'.split())
ScheduleStrength = namedtuple('ScheduleStrength', 'wins losses ties'.split())

teams = dict()
games = defaultdict(list) 
records = defaultdict(Record)
victoryStrength = defaultdict(VictoryStrength)
scheduleStrength = defaultdict(ScheduleStrength)
conferenceRecords = defaultdict(ConferenceRecord)
divisionRecords = defaultdict(DivisionRecord)
pointsFor =defaultdict(int)
pointsAgainst = defaultdict(int)

def makeTeams():
    for line in open('teams.txt'):
        data = line.split()
        team = ' '.join(data[:-3])
        div = data[-2]
        conf = data[-3]
        abbrev = data[-1]
        teams[team] = Team(abbrev, conf, div) 
        
def post(stop):
    '''
    stop is a date in yyyy-mm-dd format
    only games on or before stop are taken into account
    '''        
    with open('footballdb.html') as fin:
        text =fin.read()
    soup = BeautifulSoup(text, 'html.parser')
    rows = soup.findAll('tr')[1:]    
    playedCount = 0
    unplayedCount = 0
    for row in rows:
        data = row.contents
        try:
            date = data[0].contents[0].contents[0].split('/')
            date = date[2]+'-'+date[0]+'-'+date[1]
            home = data[1].contents[0].contents[0]
            away = data[4].contents[0].contents[0]
            homeTeam = teams[home]
            awayTeam = teams[away]
            conf = homeTeam.conference == awayTeam.conference
            div = conf and (homeTeam.division == awayTeam.division)            
            if date > stop: 
                unplayedCount += 1
                games[home].append(Game(date, home, away, conf, div, 'upcoming', 0,0,))
                games[away].append(Game(date, home, home, conf, div, 'upcoming', 0,0,)) 
                continue
        except AttributeError:    
            continue
        playedCount +=1
        homeScore = int(data[2].contents[0])
        awayScore = int(data[5].contents[0]) 
        if homeScore == awayScore:
            games[home].append(Game(date, home, away, conf, div, 'tie', homeScore, awayScore))
            games[away].append(Game(date, home, home, conf, div, 'tie', homeScore, awayScore))
        elif homeScore > awayScore:
            games[home].append(Game(date, home, away, conf, div, 'win', homeScore, awayScore))
            games[away].append(Game(date, home, home, conf, div, 'loss', awayScore, homeScore))
        else:
            games[home].append(Game(date, home, away, conf, div, 'loss', homeScore, awayScore))
            games[away].append(Game(date, home, home, conf, div, 'win', awayScore, homeScore))
        pointsFor[home] += homeScore
        pointsAgainst[home] += awayScore
        pointsFor[away] += awayScore
        pointsAgainst[away] += homeScore
    return playedCount, unplayedCount

def makeRecords():
    for team in teams:
        wins = [g for g in games[team] if g.result == 'win']
        losses = [g for g in games[team] if g.result == 'loss']
        ties = [g for g in games[team] if g.result == 'tie']
        records[team]= Record(len(wins), len(losses), len(ties))
        wins = [g for g in wins if g.conference]
        losses = [g for g in losses if g.conference]
        ties = [g for g in ties if g.conference]
        conferenceRecords[team]= ConferenceRecord(len(wins), len(losses), len(ties))
        wins = [g for g in wins if g.division]
        losses = [g for g in losses if g.division]
        ties = [g for g in ties if g.division] 
        divisionRecords[team]= DivisionRecord(len(wins), len(losses), len(ties))
        
def calcStrength():
    for team in teams:
        opponents = [g.opponent for g in games[team]]
        defeated =[g.opponent for g in games[team] if g.result == 'win']
        scheduleStrength[team] = ScheduleStrength(
            wins = sum(records[t].wins for t in opponents),
            losses = sum(records[t].losses for t in opponents),
            ties = sum(records[t].ties for t in opponents))
        victoryStrength[team] = VictoryStrength(
            wins = sum(records[t].wins for t in defeated),
            losses = sum(records[t].losses for t in defeated),
            ties = sum(records[t].ties for t in defeated))   

def pct(r):
    return (r.wins+r.ties/2)/(r.wins+r.losses+r.ties)

def startup(stop):
    makeTeams()
    p, u = post(stop)
    print(f'Stored {p} played games and {u} unplayed games') 
    makeRecords()
    calcStrength()
    
  
def lookup(team):
    if team in teams:
        return team
    try:
        return [t for t in teams if teams[t].abbreviation == team][0]
    except IndexError:
        print(f"Don't recognize {team}")
        raise
    
def compare(*args):
    try:
        args =[lookup(team) for team in args]
    except IndexError:
        return
    conferences = {teams[team].conference for team in args}
    if len(conferences)>1:
        print("Can't compare teams in different conferences")
        return
    divisions = {teams[team].division for team in args}
    if len(divisions) == 1:
        compareDivision(*args)
    elif len(divisions)==len(args):
        compareWildCard(*args)
    else:
        print('No more than one team in a division for wild card race.')
        
def compareWildCard(*args):
    print()
    print('Overall')
    for t in args:
        r = records[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    head2headSweep(*args)
    conference(*args)
    commonGames(*args)
    victory2(*args)
    schedule2(*args)
    combinedRankConference(*args)
    combinedRankOverall(*args)
    netPointsConference(*args)
    netPointsOverall(*args)
        
def compareDivision(*args):
    print()
    print('Overall')
    for t in args:
        r = records[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    head2headDivision(*args) 
    divsion(*args)
    commonGames(*args)
    conference(*args)
    victory(*args)
    schedule(*args)
    combinedRankConference(*args)
    combinedRankOverall(*args) 
    netPointsCommon(*args)
    #netPointsOverall2(team1, team2)
    
def conference(*args):
    print('Conference')
    for t in args:
        r = conferenceRecords[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()
    
def divsion(*args):
    print('Division')
    for team in args:
        divGames = [g for g in games[team] if g.division]
        wins = len([g for g in divGames if g.result=='win'])
        losses = len([g for g in divGames if g.result=='loss'])
        ties = len([g for g in divGames if g.result=='tie'])
        r = Record(wins, losses, ties)
        print(f'  {team:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()   
    
def head2headDivision(*args):
    print('\nHead to Head:')
    results = dict()
    for team in args:
        print(f'\n  {team}')
        meet = [g for g in games[team] if g.opponent in args] 
        for game in meet:
            print(f'    {game.date} vs {game.opponent}  {game.result.title()}')
        wins = len([game for game in meet if game.result == 'win'])
        losses = len([game for game in meet if game.result == 'loss'])
        ties = len([game for game in meet if game.result == 'tie'])
        results[team] = Record(wins, losses, ties)
    print()
    for team in args:
        r = results[team]
        print(f'  {team:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    print()
    
def commonGames(*args):
    opponents = { }
    results = { }
    for team in args:
        opponents[team] = {g.opponent for g in games[team]}  
    common = reduce(lambda x, y: x&y, opponents.values(), {team for team in teams})
    count = 0
    for team in args:
        count += len([g for g in games[team] if g.opponent in common])
    print('Common Opponents')
    if count < 4:
        print('  Insufficient common games')
        # Cannot happen in division
        return
    for team in args:
        print(f'  {team}')
        wins = 0
        losses = 0
        ties = 0
        for g in games[team]:
            if g.opponent in common:
                print(f'    {g.date} vs {g.opponent} {g.result.title()}')
                if g.result == 'win':
                    wins += 1
                elif g.result == 'loss':
                    losses += 1
                elif g.result == 'tie':
                    ties += 1
        results[team] = Record(wins, losses, ties) 
        print()
    for team in args:
        r = results[team]
        print(f'  {team:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    print()
        
    
def victory(*args):
    print('Strength of Victory')
    for t in args:
        r = victoryStrength[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()    
    
def schedule(*args):
    print('Strength of Schedule')
    for t in args:
        r = scheduleStrength[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()    
    
def combinedRankConference(*args):
    conf = teams[args[0]].conference
    scored = [v for v in pointsFor.items() if teams[v[0]].conference == conf]
    allowed = [v for v in pointsAgainst.items() if teams[v[0]].conference == conf]    
    scored.sort(key = lambda x:x[1], reverse=True)
    allowed.sort(key = lambda x:x[1])
    scored = [s[0] for s in scored]
    allowed = [a[0] for a in allowed]
    print('Combined Points Rank in Conference')
    print('(Lower is better)')
    for team in args:
        s = scored.index(team)+1
        a = allowed.index(team)+1 
        print(f'  {team:25s} scored {s} allowed {a} combined {a+s}')
    print()

def combinedRankOverall(*args):
    scored = [v for v in pointsFor.items()]
    allowed = [v for v in pointsAgainst.items()]    
    scored.sort(key = lambda x:x[1], reverse=True)
    allowed.sort(key = lambda x:x[1])
    scored = [s[0] for s in scored]
    allowed = [a[0] for a in allowed]
    print('Combined Points Rank Overall')
    print('(Lower is better)')
    for team in args:
        s = scored.index(team)+1
        a = allowed.index(team)+1 
        print(f'  {team:25s} scored {s} allowed {a} combined {a+s}')
    print()
        
def netPointsConference(*args):
    print('Net Points in Conference Games')
    for team in args:
        net = sum([g.scored-g.allowed for g in games[team] if g.conference])
        print(f'  {team:25s} {net}')
    print()
    
def netPointsOverall(*args):
    print('Net Points in All Games')
    for team in args:
        net = pointsFor[team] - pointsAgainst[team]
        print(f'  {team:25s} {net}')
    print()
    
def netPointsCommon(*args):
    opponents = { }
    for team in args:
        opponents[team] = {g.opponent for g in games[team]}  
        common = reduce(lambda x, y: x&y, opponents.values(), {team for team in teams})
    print('Net Points Common Games')
    for team in args:
        net = sum(g.scored - g.allowed for g in games[team] if g.opponent in common)
        print(f'  {team:25s} {net}')
    print()    
def head2headSweep(*args):
    print("Head to Head Sweep")
    others = len(args) - 1
    results = { }
    for team in args:
        common = [g for g in games[team] if g.opponent in args]
        if len(common) != others:
            print(f'  {team} did not play all others.  Not applicable.')
            return
        wins = len([g for g in common if g.result=='win'])
        losses = len([g for g in common if g.result=='loss'])
        ties = len([g for g in common if g.result=='tie'])
        results[team] = Record(wins, losses, ties)
    for team in args:
        r = results[team]
        print(f'  {team:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    print()
        
        
startup('2020-12-09')
compare('KC', 'BUF', 'PIT')
