from bs4 import BeautifulSoup
from collections import defaultdict, namedtuple
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
    
def compare2(team1, team2):
    if team1 not in teams:
        try:
            team1 = [team for team in teams if teams[team].abbreviation == team1][0]
        except IndexError:
            print(f"Don't recognize {team1}")
            return
    if team2 not in teams:
        try:
            team2 = [team for team in teams if teams[team].abbreviation == team2][0]
        except IndexError:
            print(f"Don't recognize {team2}")
            return
    if teams[team1].conference != teams[team2].conference:
        raise(ValueError("Can't compare teams in different conferences"))
    if teams[team1].division == teams[team2].division:
        compare2Division(team1, team2)
    else:
        compare2Wild(team1, team2)
        
def compare2Wild(team1, team2):
    print()
    print('Overall')
    for t in team1, team2:
        r = records[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    head2(team1, team2)
    conference2(team1, team2)
    commonGames2(team1, team2)
    victory2(team1, team2)
    schedule2(team1, team2)
    combinedRankConf2(team1, team2)
    combinedRankOverall2(team1, team2)
    netPointsConf2(team1, team2)
    netPointsOverall2(team1, team2)
        
def compare2Division(team1, team2):
    print()
    print('Overall')
    for t in team1, team2:
        r = records[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')
    head2(team1, team2) 
    divsion2(team1, team2)
    commonGames2(team1, team2)
    conference2(team1, team2)
    victory2(team1, team2)
    schedule2(team1, team2)
    combinedRankConf2(team1, team2)
    combinedRankOverall2(team1, team2) 
    netPointsCommon2(team1, team2)
    netPointsOverall2  (team1, team2)
    
def conference2(team1, team2):
    print('Conference')
    for t in team1, team2:
        r = conferenceRecords[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()
    
def divsion2(team1, team2):
    print('Division')
    for team in team1, team2:
        divGames = [g for g in games[team] if g.division]
        wins = len([g for g in divGames if g.result=='win'])
        losses = len([g for g in divGames if g.result=='loss'])
        ties = len([g for g in divGames if g.result=='tie'])
        r = Record(wins, losses, ties)
        print(f'  {team:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()   
    
def head2(team1, team2):
    print('\nHead to Head:')
    meet = [g for g in games[team1] if g.opponent == team2] 
    if not meet:
        print('  Not Applicable\n')
        return
    for game in meet:
        print(f'  {game.date} ', end='')
        if game.result=='upcoming':
            print('Upcoming')
        elif game.result == 'tie':
            print('Tie')
        elif game.result == 'win':
            print( f'Winner {team1}')
        else:
            print(f'Winner {team2}')
    print()    
    
def commonGames2(team1, team2):
    opponents = { }
    for team in team1, team2:
        opponents[team] = [g.opponent for g in games[team]]  
    common = [team for team in teams if team in opponents[team1] and team in opponents[team2]]
    print('Common Opponents')
    for team in team1, team2:
        print(f'  {team}')
        wins = 0
        losses = 0
        ties = 0
        for g in games[team]:
            if g.opponent in common:
                print(f'    {g.date} {g.opponent} {g.result}')
                if g.result == 'win':
                    wins += 1
                elif g.result == 'loss':
                    losses += 1
                elif g.result == 'tie':
                    ties += 1
        r = Record(wins, losses, ties)
        print (f'  {wins}-{losses}-{ties} {pct(r):.3f}%') 
        print()
    
def victory2(team1, team2):
    print('Strength of Victory')
    for t in team1, team2:
        r = victoryStrength[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()    
    
def schedule2(team1, team2):
    print('Strength of Schedule')
    for t in team1, team2:
        r = scheduleStrength[t]
        print(f'  {t:25s} {r.wins}-{r.losses}-{r.ties} {pct(r):.3f}%')  
    print()    
    
def combinedRankConf2(team1, team2):
    conf = teams[team1].conference
    scored = [v for v in pointsFor.items() if teams[v[0]].conference == conf]
    allowed = [v for v in pointsAgainst.items() if teams[v[0]].conference == conf]    
    scored.sort(key = lambda x:x[1], reverse=True)
    allowed.sort(key = lambda x:x[1])
    scored = [s[0] for s in scored]
    allowed = [a[0] for a in allowed]
    print('Combined Points Rank in Conference')
    print('(Lower is better)')
    for team in team1, team2:
        s = scored.index(team)+1
        a = allowed.index(team)+1 
        print(f'  {team:25s} scored {s} allowed {a} combined {a+s}')
    print()

def combinedRankOverall2(team1, team2):
    scored = [v for v in pointsFor.items()]
    allowed = [v for v in pointsAgainst.items()]    
    scored.sort(key = lambda x:x[1], reverse=True)
    allowed.sort(key = lambda x:x[1])
    scored = [s[0] for s in scored]
    allowed = [a[0] for a in allowed]
    print('Combined Points Rank Overall')
    print('(Lower is better)')
    for team in team1, team2:
        s = scored.index(team)+1
        a = allowed.index(team)+1 
        print(f'  {team:25s} scored {s} allowed {a} combined {a+s}')
    print()
        
def netPointsConf2(team1, team2):
    print('Net Points in Conference Games')
    for team in team1, team2:
        net = sum([g.scored-g.allowed for g in games[team] if g.conference])
        print(f'  {team:25s} {net}')
    print()
    
def netPointsOverall2(team1, team2):
    print('Net Points in All Games')
    for team in team1, team2:
        net = pointsFor[team] - pointsAgainst[team]
        print(f'  {team:25s} {net}')
    print()
    
def netPointsCommon2(team1, team2):
    opponents = { }
    for team in team1, team2:
        opponents[team] = [g.opponent for g in games[team]]  
    common = [team for team in teams if team in opponents[team1] and team in opponents[team2]]
    print('Net Points Common Games')
    for team in team1, team2:
        net = sum(g.scored - g.allowed for g in games[team] if g.opponent in common)
        print(f'  {team:25s} {net}')
    print()    
          
startup('2020-12-09')
compare2('KC', 'LV')
