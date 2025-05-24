import os

# Cấu hình cơ sở dữ liệu
DB_PATH = 'dictionary.db'

# Cấu hình thư mục
CACHE_DIR = 'cache'
TEMP_DIR = 'temp'

# Đảm bảo thư mục tồn tại
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# User agents để tránh bị chặn
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
]

# Nguồn dữ liệu GitHub
GITHUB_SOURCES = [
    {
        "name": "vietnamese-wordlist",
        "url": "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet74K.txt",
        "type": "vi-words",
        "format": "txt"
    },
    {
        "name": "english-wordnet",
        "url": "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.dic",
        "type": "en-words",
        "format": "txt"
    },
    {
        "name": "en-vi-dict",
        "url": "https://raw.githubusercontent.com/undertheseanlp/dictionary/master/dictionary/data/en_vi_dict.txt",
        "type": "en-vi",
        "format": "txt"
    },
    {
        "name": "vi-en-dict",
        "url": "https://raw.githubusercontent.com/undertheseanlp/dictionary/master/dictionary/data/vi_en_dict.txt",
        "type": "vi-en",
        "format": "txt"
    },
    {
        "name": "wordnet-vi",
        "url": "https://raw.githubusercontent.com/vunb/vntk/master/data/resources/dictionaries/vi-en/wordnet_synset.txt",
        "type": "vi-en",
        "format": "txt"
    }
]

# Nguồn dữ liệu OPUS
OPUS_SOURCES = [
    {
        "name": "OpenSubtitles",
        "url": "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/moses/en-vi.txt.zip",
        "alignment": "en-vi"
    },
    {
        "name": "Bible",
        "url": "https://object.pouta.csc.fi/OPUS-Bible/v1.0/moses/en-vi.txt.zip", 
        "alignment": "en-vi"
    },
    {
        "name": "QED",
        "url": "https://object.pouta.csc.fi/OPUS-QED/v2.0a/moses/en-vi.txt.zip",
        "alignment": "en-vi"
    }
]

# Dữ liệu cho việc làm giàu
COMMON_POS = {
    "the": "article", "a": "article", "an": "article",
    "is": "verb", "are": "verb", "was": "verb", "were": "verb", "be": "verb",
    "have": "verb", "has": "verb", "had": "verb", "do": "verb", "does": "verb", "did": "verb",
    "go": "verb", "goes": "verb", "went": "verb", "say": "verb", "says": "verb", "said": "verb",
    "good": "adjective", "bad": "adjective", "big": "adjective", "small": "adjective",
    "quickly": "adverb", "slowly": "adverb", "happily": "adverb", "sadly": "adverb"
}

COMMON_PRONUNCIATIONS = {
    "the": "/ðə/", "a": "/ə/", "an": "/ən/",
    "is": "/ɪz/", "are": "/ɑr/", "was": "/wəz/", "were": "/wər/", 
    "have": "/hæv/", "has": "/hæz/", "had": "/hæd/",
    "go": "/ɡoʊ/", "say": "/seɪ/", "see": "/siː/",
    "good": "/ɡʊd/", "bad": "/bæd/", "big": "/bɪɡ/", "small": "/smɔːl/"
}

COMMON_EXAMPLES = {
    "the": "The book is on the table.",
    "a": "I saw a dog in the park.",
    "an": "She brought an umbrella with her.",
    "is": "He is a doctor.",
    "are": "They are my friends.",
    "go": "I go to school every day.",
    "good": "The food was very good."
}