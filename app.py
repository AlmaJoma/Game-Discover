import os
import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from collections import Counter
import requests
from flask import Flask, render_template, request, session, jsonify, make_response
from flask_session import Session
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# disclaimer: this project has been made with the aid of AI with the implementation of translations, the advanced filtering system and the implementation of the search box

TRANSLATIONS = {
    'es': {
        'discover_experience': 'Descubre tu próxima experiencia',
        'take_test': 'Toma el Test',
        'no_idea_text': '¿No tienes idea de que jugar ahora? Este simple test fue creado con el propósito de generar recomendaciones basadas en tus elecciones y juegos jugados anteriormente',
        'rawg_text': 'hecho con la base de datos RAWG, ahora puedes descubrir opciones que podrian ser de tu interés, simplemente dale al botón y comienza!',
        'recommendations': 'Recomendaciones:',
        'genres': 'Géneros:',
        'rating': 'Rating:',
        'released': 'Released:',
        'more_btn': 'Más',
        'platform_question': '¿Qué dispositivo usas para jugar principalmente?',
        'age_question': '¿Qué tan nuevo tiene que ser un videojuego para que te llame la atención?',
        'age_recent': 'Reciente',
        'age_10years': 'Últimos 10 años',
        'age_retro': 'Retro',
        'age_no_pref': 'Sin preferencia',
        'playtime_question': '¿Cuántas horas prefieres invertir en un juego (totales)?',
        'playtime_short': 'Menos de 15',
        'playtime_medium': '15 - 40',
        'playtime_long': '40+',
        'players_question': '¿Prefieres una experiencia en solitario o con otras personas?',
        'players_solo': 'Solo',
        'players_multi': 'Con otros',
        'pace_question': '¿Qué ritmo prefieres?',
        'pace_fast': 'Rápido y con acción',
        'pace_relaxed': 'Tranquilo y relajante',
        'story_question': '¿Qué te atrae más de una historia?',
        'story_choices': 'La toma de decisiones y distintas rutas',
        'story_atmosphere': 'La atmósfera',
        'story_characters': 'Los personajes',
        'story_mystery': 'El misterio',
        'fun_question': '¿Qué valoras más para divertirte?',
        'fun_skill': 'Destreza y precisión',
        'fun_thinking': 'Resolver problemas y planificación',
        'exploration_question': '¿Prefieres explorar por un mundo abierto o algo más lineal?',
        'exploration_open': 'Explorar',
        'exploration_linear': 'Lineal',
        'joy_question': '¿Qué te hace disfrutar más un juego?',
        'joy_freedom': 'Sentirme libre',
        'joy_challenge': 'Sentirme desafiado',
        'joy_funny': 'Reírme o divertirme',
        'joy_emotional': 'Conectarme emocionalmente',
        'joy_competitive': 'Competir con otros',
        'visual_question': '¿Qué estilo visual prefieres?',
        'visual_pixel': 'Pixel art',
        'visual_anime': 'Anime',
        'visual_stylized': 'Estilizado',
        'visual_realistic': 'Realista',
        'visual_minimalist': 'Minimalista',
        'visual_lowpoly': 'Low poly',
        'phrase_question': 'Escoge la frase que más te atraiga',
        'phrase_1': 'Quiero adrenalina y dominar con habilidad',
        'phrase_2': 'Quiero perderme en una historia y mejorar mi personaje',
        'phrase_3': 'Quiero pensar, optimizar y resolver',
        'phrase_4': 'Quiero partidas rápidas, fáciles y divertidas',
        'add_games_question': '¿Te gustaría añadir juegos que has jugado anteriormente?',
        'search_placeholder': 'Buscar juegos...',
        'clear_games': 'Limpiar juegos seleccionados',
        'submit': 'Enviar',
        'searching': 'Buscando...',
        'no_results': 'No se encontraron juegos'
    },
    'en': {
        'discover_experience': 'Discover your next experience',
        'take_test': 'Take the Test',
        'no_idea_text': "Don't know what to play now? This simple test was created to generate recommendations based on your choices and previously played games",
        'rawg_text': 'made with the RAWG database, now you can discover options that might interest you, just click the button and start!',
        'recommendations': 'Recommendations:',
        'genres': 'Genres:',
        'rating': 'Rating:',
        'released': 'Released:',
        'more_btn': 'More',
        'platform_question': 'What device do you mainly use to play?',
        'age_question': 'How new does a video game need to be to catch your attention?',
        'age_recent': 'Recent',
        'age_10years': 'Last 10 years',
        'age_retro': 'Retro',
        'age_no_pref': 'No preference',
        'playtime_question': 'How many hours do you prefer to invest in a game (total)?',
        'playtime_short': 'Less than 15',
        'playtime_medium': '15 - 40',
        'playtime_long': '40+',
        'players_question': 'Do you prefer a solo experience or with other people?',
        'players_solo': 'Solo',
        'players_multi': 'With others',
        'pace_question': 'What pace do you prefer?',
        'pace_fast': 'Fast and action-packed',
        'pace_relaxed': 'Calm and relaxing',
        'story_question': 'What attracts you most about a story?',
        'story_choices': 'Decision-making and different paths',
        'story_atmosphere': 'The atmosphere',
        'story_characters': 'The characters',
        'story_mystery': 'The mystery',
        'fun_question': 'What do you value most for fun?',
        'fun_skill': 'Skill and precision',
        'fun_thinking': 'Problem solving and planning',
        'exploration_question': 'Do you prefer exploring an open world or something more linear?',
        'exploration_open': 'Explore',
        'exploration_linear': 'Linear',
        'joy_question': 'What makes you enjoy a game the most?',
        'joy_freedom': 'Feeling free',
        'joy_challenge': 'Feeling challenged',
        'joy_funny': 'Laughing or having fun',
        'joy_emotional': 'Connecting emotionally',
        'joy_competitive': 'Competing with others',
        'visual_question': 'What visual style do you prefer?',
        'visual_pixel': 'Pixel art',
        'visual_anime': 'Anime',
        'visual_stylized': 'Stylized',
        'visual_realistic': 'Realistic',
        'visual_minimalist': 'Minimalist',
        'visual_lowpoly': 'Low poly',
        'phrase_question': 'Choose the phrase that appeals to you most',
        'phrase_1': 'I want adrenaline and skill mastery',
        'phrase_2': 'I want to get lost in a story and improve my character',
        'phrase_3': 'I want to think, optimize and solve',
        'phrase_4': 'I want quick, easy and fun matches',
        'add_games_question': 'Would you like to add games you have played before?',
        'search_placeholder': 'Search games...',
        'clear_games': 'Clear selected games',
        'submit': 'Submit',
        'searching': 'Searching...',
        'no_results': 'No games found'
    }
}

def get_language():
    """Obtiene el idioma de la cookie o usa 'es' por defecto"""
    return request.cookies.get('language', 'es')

def get_translations():
    """Devuelve las traducciones para el idioma actual"""
    lang = get_language()
    return TRANSLATIONS.get(lang, TRANSLATIONS['es'])

# -----------------------
# Config
# -----------------------
RAWG_BASE = 'https://api.rawg.io/api'
MAX_WORKERS = 10

# configurables
MAX_CANDIDATES = 3000
MAX_PAGES_PER_QUERY = 6

# -----------------------
# Utilidades
# -----------------------

def safe_get(d, key, default=None):
    v = d.get(key, default)
    return v if v is not None else default


@lru_cache(maxsize=1024)
def obtener_juego_rawg(game_id):
    url = f"{RAWG_BASE}/games/{game_id}"
    params = {'key': API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_games(params):
    """Llamada simple a RAWG /games con manejo de errores y rate limit básico."""
    url = f"{RAWG_BASE}/games"
    params['key'] = API_KEY
    try:
        r = requests.get(url, params=params, timeout=12)
        data = r.json()
        return data
    except Exception:
        return {'results': []}

AGE_FILTERS = {
    '1': (2020, 9999),
    '2': (2015, 9999),
    '3': (1970, 2005),
    '4': None
}

PLAYTIME_FILTERS = {
    'short': (0, 15),
    'medium': (15, 40),
    'long': (40, 9999)
}

PLAYSTYLE_TAGS = {
    'solo': ['Singleplayer'],
    'multi': ['Multiplayer', 'Co-op']
}

PACE_TAGS = {
    'fast': ['Fast-Paced', 'Action'],
    'relaxed': ['Casual', 'Cozy', 'Relaxing']
}

STORY_TAGS = {
    'choices': ['Choices Matter', 'Multiple Endings'],
    'atmosphere': ['Atmospheric', 'Immersive'],
    'characters': ['Character Customization', 'Story Rich'],
    'mystery': ['Mystery', 'Detective']
}

FUN_GENRES = {
    'skill': ['Action', 'Shooter', 'Fighting', 'Racing', 'Platformer'],
    'thinking': ['Puzzle', 'Strategy', 'Simulation', 'Adventure', 'Role-Playing']
}

PHRASE_GENRES = {
    '1': ['Action', 'Shooter', 'Fighting', 'Racing'],
    '2': ['Role-Playing', 'Adventure', 'Platformer'],
    '3': ['Strategy', 'Simulation', 'Puzzle'],
    '4': ['Casual', 'Arcade', 'Sports']
}

VISUAL_TAGS = {
    'pixel': ['Pixel Graphics', 'Retro'],
    'anime': ['Anime'],
    'stylized': ['Stylized', 'Cartoony'],
    'realistic': ['Realistic', 'Photorealistic'],
    'minimalist': ['Minimalist', 'Abstract'],
    'lowpoly': ['Low Poly', '3D']
}

EXPLORATION_TAGS = {
    'open': ['Open World', 'Sandbox', 'Exploration'],
    'linear': ['Linear', 'Story Rich', 'Narrative']
}

JOY_TAGS = {
    'freedom': ['Open World', 'Sandbox', 'Freedom'],
    'challenge': ['Difficult', 'Souls-like', 'Challenging'],
    'funny': ['Comedy', 'Funny', 'Humor'],
    'emotional': ['Emotional', 'Story Rich', 'Drama'],
    'competitive': ['Competitive', 'PvP', 'eSports']
}

# -----------------------
# Feature engineering
# -----------------------

_feature_lock = threading.Lock()


def text_keywords(name):
    if not name:
        return []
    name = re.sub(r"[^a-zA-Z0-9 ]", ' ', name).lower()
    parts = [p for p in name.split() if len(p) > 2]
    stop = {'the', 'and', 'for', 'with', 'game', 'edition', 'remastered'}
    return [p for p in parts if p not in stop]


def game_to_vector(game):
    """Devuelve un dict {feature:weight} representando el juego."""
    vec = {}

    # géneros
    for g in game.get('genres', []) or []:
        name = g.get('name') if isinstance(g, dict) else g
        if name:
            vec[f'genre:{name.lower()}'] = 1.0

    # tags
    for t in game.get('tags', []) or []:
        name = t.get('name') if isinstance(t, dict) else t
        if name:
            vec[f'tag:{name.lower()}'] = 1.0

    # developers
    for d in game.get('developers', []) or []:
        name = d.get('name') if isinstance(d, dict) else d
        if name:
            vec[f'dev:{name.lower()}'] = 1.0

    # esrb
    esrb = game.get('esrb_rating')
    if esrb and isinstance(esrb, dict):
        rname = esrb.get('name')
        if rname:
            vec[f'esrb:{rname.lower()}'] = 1.0

    # keywords del nombre
    for kw in text_keywords(game.get('name') or ''):
        vec[f'kw:{kw}'] = 1.0

    # metacritic
    meta = game.get('metacritic') or 0
    if meta:
        vec['meta'] = meta / 100.0

    # playtime
    pt = game.get('playtime') or 0
    vec['playtime'] = min(1.0, pt / 60.0)

    return vec


def normalize_vec(vec):
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return vec
    return {k: v / norm for k, v in vec.items()}


def cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    s = 0.0
    for k, v in vec_a.items():
        s += v * vec_b.get(k, 0.0)
    return s

def construir_perfil_jugados(jugados_ids):
    juegos = []
    for gid in jugados_ids:
        try:
            juegos.append(obtener_juego_rawg(gid))
        except Exception:
            pass

    counter_tags = Counter()
    counter_genres = Counter()
    counter_devs = Counter()
    keywords = Counter()
    metas = []
    playtimes = []

    for d in juegos:
        for t in d.get('tags', []) or []:
            if isinstance(t, dict):
                counter_tags[t.get('name')] += 1
            else:
                counter_tags[t] += 1
        for g in d.get('genres', []) or []:
            if isinstance(g, dict):
                counter_genres[g.get('name')] += 1
            else:
                counter_genres[g] += 1
        for dev in d.get('developers', []) or []:
            if isinstance(dev, dict):
                counter_devs[dev.get('name')] += 1
            else:
                counter_devs[dev] += 1
        for kw in text_keywords(d.get('name') or ''):
            keywords[kw] += 1
        if d.get('metacritic'):
            metas.append(d.get('metacritic'))
        if d.get('playtime'):
            playtimes.append(d.get('playtime'))

    total_tags = sum(counter_tags.values()) or 1
    total_genres = sum(counter_genres.values()) or 1
    total_devs = sum(counter_devs.values()) or 1
    total_kw = sum(keywords.values()) or 1

    perfil = {}
    for k, v in counter_tags.items():
        perfil[f'tag:{k.lower()}'] = (v / total_tags) * 1.2
    for k, v in counter_genres.items():
        perfil[f'genre:{k.lower()}'] = (v / total_genres) * 1.6
    for k, v in counter_devs.items():
        perfil[f'dev:{k.lower()}'] = (v / total_devs) * 1.4
    for k, v in keywords.items():
        perfil[f'kw:{k}'] = (v / total_kw) * 1.0
    if metas:
        perfil['meta'] = (sum(metas) / len(metas)) / 100.0
    if playtimes:
        perfil['playtime'] = min(1.0, (sum(playtimes) / len(playtimes)) / 60.0)

    perfil = normalize_vec(perfil)
    return perfil

def build_search_params(base, extra):
    params = base.copy()
    params.update(extra)
    return params


def buscar_juegos_amplio_v2(filtros, top_genres, top_tags, excluir_ids):
    candidates = {}
    base = {
        'page_size': 40,
        'search_precise': True,
        'exclude_additions': True
    }

    if filtros.get('platform'):
        base['platforms'] = filtros['platform']

    if filtros.get('year'):
        y1, y2 = filtros['year']
        base['dates'] = f"{y1}-01-01,{y2}-12-31"

    # Estrategia 1: Búsqueda por géneros principales
    queries = []
    for g in top_genres[:3]:
        slugg = g.lower().replace(' ', '-')
        queries.append({**base, 'genres': slugg, 'ordering': '-rating'})
        queries.append({**base, 'genres': slugg, 'ordering': '-metacritic'})

    # Estrategia 2: Búsqueda por tags principales (convertir a slug)
    for t in top_tags[:3]:
        slug_tag = t.lower().replace(' ', '-')
        queries.append({**base, 'tags': slug_tag, 'ordering': '-rating'})

    # Estrategia 3: Búsquedas complementarias
    queries.append({**base, 'ordering': '-rating'})
    queries.append({**base, 'ordering': '-metacritic'})

    # Si hay filtro de playtime, buscar específicamente
    if filtros.get('playtime'):
        pt_min, pt_max = filtros['playtime']
        queries.append({**base, 'ordering': '-rating'})

    # Limitar queries
    if len(queries) > 50:
        queries = queries[:50]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = []
        for params in queries:
            futures.append(ex.submit(fetch_pages_for_params, params, MAX_PAGES_PER_QUERY))

        for fut in as_completed(futures):
            try:
                lista = fut.result()
                for g in lista:
                    if g['id'] in excluir_ids:
                        continue
                    candidates[g['id']] = g
                    if len(candidates) >= MAX_CANDIDATES:
                        break
                if len(candidates) >= MAX_CANDIDATES:
                    break
            except Exception:
                continue

    return list(candidates.values())


def fetch_pages_for_params(params, max_pages=4):
    out = []
    params = params.copy()
    for page in range(1, max_pages + 1):
        params['page'] = page
        data = fetch_games(params)
        for r in data.get('results', []):
            out.append(r)
        if not data.get('next'):
            break
    return out

def rerank_and_diversify(candidates, user_vec, filtros, top_n=15):
    scored = []

    for g in candidates:
        gv = game_to_vector(g)
        gv = normalize_vec(gv)
        sim = cosine_similarity(user_vec, gv)

        # Penalización por extrema popularidad
        added = g.get('added', 0) or 0
        pop_penalty = 0.0
        if added > 250000:
            pop_penalty = 0.20
        elif added > 100000:
            pop_penalty = 0.10

        # Bonus por año
        year_bonus = 0.0
        if filtros.get('year') and g.get('released'):
            try:
                year = int(g['released'][:4])
                y1, y2 = filtros['year']
                if y1 <= year <= y2:
                    year_bonus = 0.08
            except Exception:
                pass

        # Bonus por playtime match
        playtime_bonus = 0.0
        if filtros.get('playtime') and g.get('playtime'):
            pt_min, pt_max = filtros['playtime']
            g_pt = g.get('playtime', 0)
            if pt_min <= g_pt <= pt_max:
                playtime_bonus = 0.10

        # Combinar score
        score = sim - pop_penalty + year_bonus + playtime_bonus
        score += (g.get('rating') or 0) * 0.003

        scored.append((score, g))

    scored.sort(reverse=True, key=lambda x: x[0])

    # Diversificación greedy
    final = []
    genre_counts = Counter()
    i = 0
    while len(final) < top_n and i < len(scored):
        score, g = scored[i]
        i += 1
        genres = [x.get('name') for x in g.get('genres', []) or []]
        primary = genres[0] if genres else 'other'

        # Permitir hasta 3 por género, pero solo si el score es bueno
        if genre_counts[primary] >= 3:
            if score < 0.2:
                continue

        genre_counts[primary] += 1
        final.append((score, g))

    # Rellenar si falta
    if len(final) < top_n:
        for s, g in scored:
            if (s, g) not in final:
                final.append((s, g))
                if len(final) >= top_n:
                    break

    return [g for s, g in final[:top_n]]

@app.route('/')
def index():
    return render_template('index.html', t=get_translations(), lang=get_language())


@app.route('/gamequestionnaire', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        filtros = build_filters_from_form(request.form)

        # Obtener juegos seleccionados
        jugados = session.get('juegos_seleccionados', [])
        excluir_ids = {j['id'] for j in jugados}

        # Construir perfil SIN CACHE (se actualiza cada vez)
        jugados_ids = [j['id'] for j in jugados]
        user_vec = construir_perfil_jugados(jugados_ids) if jugados_ids else {}

        # Añadir respuestas del form al perfil
        boost_vec = build_vec_from_form(filtros)

        # Combinar vectores
        if user_vec:
            combined_vec = merge_and_normalize(user_vec, boost_vec, a=0.6, b=0.4)
        else:
            combined_vec = boost_vec

        # Extraer top géneros y tags
        top_genres = [k.split(':',1)[1] for k, v in sorted(combined_vec.items(), key=lambda x: x[1], reverse=True) if k.startswith('genre:')][:4]
        top_tags = [k.split(':',1)[1] for k, v in sorted(combined_vec.items(), key=lambda x: x[1], reverse=True) if k.startswith('tag:')][:4]

        if not top_genres:
            top_genres = ['action', 'adventure', 'indie']
        if not top_tags:
            top_tags = ['singleplayer', 'atmospheric']

        # Buscar candidatos
        candidates = buscar_juegos_amplio_v2(filtros, top_genres, top_tags, excluir_ids)

        # Re-rankear
        resultados = rerank_and_diversify(candidates, combined_vec, filtros, top_n=15)

        return render_template('result.html', juegos=resultados, t=get_translations(), lang=get_language())
    else:
        plataformas = obtener_plataformas_safe()
        principales = [p for p in plataformas if p['name'] in {'PC','PlayStation 5','Xbox Series S/X','Nintendo Switch'}]
        restantes = [p for p in plataformas if p['name'] not in {x['name'] for x in principales}]
        return render_template('test.html', principales=principales, restantes=restantes, t=get_translations(), lang=get_language())

@app.route('/set_language/<lang>')
def set_language(lang):
    """Establece el idioma en una cookie"""
    if lang not in ['es', 'en']:
        lang = 'es'

    # Redirigir a la página de origen o al index
    redirect_url = request.referrer or '/'

    response = make_response(jsonify({'success': True, 'language': lang}))
    # Cookie que dura 1 año
    response.set_cookie('language', lang, max_age=365*24*60*60)

    return response

def build_filters_from_form(form):
    tags = []
    genres = []
    platform = form.get('platform') or form.get('platform_extra')
    age_code = form.get('age_filter')
    year_filter = AGE_FILTERS.get(age_code)
    play_code = form.get('playtime')
    playtime_range = PLAYTIME_FILTERS.get(play_code)

    # Tags basados en respuestas
    tags += PLAYSTYLE_TAGS.get(form.get('players'), [])
    tags += PACE_TAGS.get(form.get('pace'), [])
    tags += STORY_TAGS.get(form.get('story'), [])
    tags += VISUAL_TAGS.get(form.get('visual'), [])
    tags += EXPLORATION_TAGS.get(form.get('exploration'), [])  # NUEVO
    tags += JOY_TAGS.get(form.get('joy'), [])  # NUEVO

    # Géneros
    genres += FUN_GENRES.get(form.get('fun'), [])
    genres += PHRASE_GENRES.get(form.get('phrase'), [])

    return {
        'platform': platform,
        'year': year_filter,
        'playtime': playtime_range,
        'tags': tags,
        'genres': genres
    }


def build_vec_from_form(filtros):
    """Construye vector de preferencias desde el formulario"""
    vec = {}

    # Tags con peso alto
    for t in filtros.get('tags', []):
        key = f'tag:{t.lower()}'
        vec[key] = vec.get(key, 0) + 1.5

    # Géneros con peso muy alto
    for g in filtros.get('genres', []):
        key = f'genre:{g.lower()}'
        vec[key] = vec.get(key, 0) + 2.0

    # Playtime como feature
    if filtros.get('playtime'):
        pt_min, pt_max = filtros['playtime']
        avg = (pt_min + pt_max) / 2
        vec['playtime'] = min(1.0, avg / 60.0)

    return normalize_vec(vec)


def merge_and_normalize(a_vec, b_vec, a=0.7, b=0.3):
    merged = {}
    for k, v in a_vec.items():
        merged[k] = merged.get(k, 0) + v * a
    for k, v in b_vec.items():
        merged[k] = merged.get(k, 0) + v * b
    return normalize_vec(merged)


# -----------------------
# Plataformas cache
# -----------------------

_platforms_cache = None


def obtener_plataformas_safe():
    global _platforms_cache
    if _platforms_cache is not None:
        return _platforms_cache
    url = f"{RAWG_BASE}/platforms"
    params = {'key': API_KEY, 'page_size': 40}
    out = []
    while url:
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            for p in data.get('results', []):
                out.append({'id': p['id'], 'name': p['name']})
            url = data.get('next')
            params = {}
        except Exception:
            break
    _platforms_cache = out
    return out


# -----------------------
# Endpoints para búsqueda/selección
# -----------------------

@app.route('/buscar_juegos')
def buscar_juegos():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    url = f"{RAWG_BASE}/games"
    params = {'key': API_KEY, 'search': query, 'page_size': 10}
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        juegos = [{'id': j['id'], 'nombre': j['name'], 'imagen': j.get('background_image')} for j in data.get('results', [])]
        return jsonify(juegos)
    except Exception:
        return jsonify([])


@app.route('/agregar_juego', methods=['POST'])
def agregar_juego():
    if 'juegos_seleccionados' not in session:
        session['juegos_seleccionados'] = []
    juego = request.json
    if not any(j['id'] == juego['id'] for j in session['juegos_seleccionados']):
        session['juegos_seleccionados'].append(juego)
        session.modified = True
    return jsonify({'success': True})


@app.route('/eliminar_juego', methods=['POST'])
def eliminar_juego():
    if 'juegos_seleccionados' not in session:
        return jsonify({'success': False})
    juego_id = request.json.get('id')
    session['juegos_seleccionados'] = [j for j in session['juegos_seleccionados'] if j['id'] != juego_id]
    session.modified = True
    return jsonify({'success': True})


@app.route('/obtener_juegos_seleccionados')
def obtener_juegos_seleccionados():
    return jsonify(session.get('juegos_seleccionados', []))


@app.route('/limpiar_sesion', methods=['POST'])
def limpiar_sesion():
    """Endpoint para limpiar los juegos seleccionados"""
    session['juegos_seleccionados'] = []
    session.modified = True
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True)
