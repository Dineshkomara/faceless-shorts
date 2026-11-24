#!/usr/bin/env python3
"""Trend Hunter - Live and curated topic discovery for YouTube Shorts.

Supports both channels:
  1. Curiography (English): Retellable concepts across psychology, behavior, body/brain,
     physical science, history, and engineering; fresh live stories are ranked against the ledger.
  2. Asakthi (Telugu): Curated, rich folklore, temple mysteries, epic Puranic feats,
     and tradition science rooted in Sanatana Dharma & Telugu heritage.

Usage:
  python3 trend_hunter.py                    # Top trending English topics
  python3 trend_hunter.py --channel te       # Telugu temple & mythology trends
  python3 trend_hunter.py --style cinematic-what-if  # Specific runnable English style
  python3 trend_hunter.py --json             # Output structured JSON
"""

import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "topics-done.md"

FEEDS = [
    {
        "source": "Google Trends",
        "url": "https://trends.google.com/trending/rss?geo=US",
        "type": "google_trends"
    },
    {
        "source": "ScienceDaily",
        "url": "https://www.sciencedaily.com/rss/top/science.xml",
        "type": "science_daily"
    },
    {
        "source": "Phys.org",
        "url": "https://phys.org/rss-feed/breaking/",
        "type": "phys_org"
    }
]

# English style genre keywords for matching
GENRE_KEYWORDS = {
    "engineering-explainer": ["engineering", "architecture", "bridge", "building", "ancient", "physics", "machine", "structure", "history", "monument", "construction", "materials"],
    "cinematic-what-if": ["memory", "attention", "perception", "taste", "smell", "hearing", "vision", "reaction", "reflex", "sleep", "pain", "touch", "strength", "metabolism", "emotion", "aging", "healing", "balance", "human", "brain", "body", "psychology"],
    "tall-tale": ["bizarre", "accidentally", "lawsuit", "millionaire", "lottery", "mythology", "legend", "fool", "hoax", "con", "stole", "genius", "curse", "god", "story", "survival"],
}

# Negative filters for English
EXCLUDE_WORDS = [
    "election", "biden", "trump", "senate", "congress", "democrat", "republican",
    "parliament", "football", "nfl", "nba", "cricket", "score", "vs", "quarterback",
    "stock", "nasdaq", "shares", "earnings", "box office", "divorce", "dating"
]

# Rich catalog of curated Telugu mythology, temple mysteries, and tradition lore
TELUGU_TOPICS_CATALOG = [
    {
        "id": "lepakshi-pillar",
        "title": "లేపాక్షి గుడిలో వేలాడే స్తంభం: బ్రిటిష్ ఇంజనీర్లకే అంతుచిక్కని శిల్పకళా రహస్యం",
        "english_title": "The Mystery Behind Lepakshi's Hanging Pillar",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "వీరభద్రస్వామి (Veerabhadra)",
        "source": "తెలుగు శిల్పకళా రహస్యాలు",
        "summary": "ఆంధ్రప్రదేశ్‌లోని లేపాక్షి వీరభద్రాలయంలో ఉన్న 70 స్తంభాలలో ఒకటి నేలను తాకకుండా గాల్లో వేలాడుతుంది. బ్రిటిష్ కాలంలో ఒక ఇంజనీర్ దీన్ని పరిశోధించడానికి ప్రయత్నించి విఫలమయ్యాడు. ఈ స్తంభం కిందనుంచి వస్త్రం లేదా కాగితం తీసినా సులభంగా దూరిపోతుంది.",
        "curiosity_score": 10,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "లేపాక్షి గుడిలో ఈ ఒక్క స్తంభం నేలను తాకకుండా గాల్లో ఎలా వేలాడుతోంది?",
            "బ్రిటిష్ ఇంజనీర్లకే అంతుచిక్కని తెలుగు ప్రాచీన ఆర్కిటెక్చర్ రహస్యం ఇది!",
            "70 స్తంభాల్లో ఈ ఒక్క స్తంభాన్ని కదిలిస్తే మొత్తం గుడి ఎందుకు కదులుతుంది?"
        ]
    },
    {
        "id": "ramappa-floating-bricks",
        "title": "రామప్ప దేవాలయం: నీటిపై తేలియాడే ఇటుకల అద్భుత ప్రాచీన తెలుగు ఆర్కిటెక్చర్",
        "english_title": "Ramappa Temple: The Ancient Floating Bricks of Kakatiya Dynasty",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "రామలింగేశ్వర స్వామి (Ramappa)",
        "source": "కాకతీయ రాజవంశ చరిత్ర & యునెస్కో హెరిటేజ్",
        "summary": "వరంగల్ సమీపంలోని 800 ఏళ్ల నాటి రామప్ప ఆలయ నిర్మాణంలో వాడిన ఇటుకలు నీటిలో వేస్తే మునగకుండా తేలుతాయి. భూకంపాలు వచ్చినా తట్టుకునే శాండ్‌బాక్స్ టెక్నాలజీతో నిర్మించిన ఈ ఆలయాన్ని యునెస్కో ప్రపంచ వారసత్వ సంపదగా గుర్తించింది.",
        "curiosity_score": 10,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "ఈ గుడిలోని ఇటుకలు నీటిలో వేస్తే మునగకుండా ఎందుకు తేలుతాయి?",
            "800 ఏళ్ల క్రితమే కాకతీయులు వాడిన ఎర్త్‌క్వేక్-రెసిస్టెంట్ శాండ్‌బాక్స్ టెక్నాలజీ!",
            "యునెస్కో సైతం ఆశ్చర్యపోయిన ప్రాచీన తెలుగు శిల్పి రామప్ప ఇంజనీరింగ్ అద్భుతం!"
        ]
    },
    {
        "id": "puri-jagannath-flag",
        "title": "పూరి జగన్నాథ ఆలయం: గాలికి ఎదురుగా ఎగిరే పతాకం & అంతుచిక్కని వింతలు",
        "english_title": "Puri Jagannath: The Flag Flying Against the Wind",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "జగన్నాథుడు (Lord Jagannath)",
        "source": "క్షేత్ర మహిమలు",
        "summary": "పూరి ఆలయ గోపురంపై ఉన్న పతాకం గాలి వీచే దిశకు పూర్తి వ్యతిరేక దిశలో ఎగురుతుంది. ఆలయ గోపురం నీడ ఎప్పుడూ నేలపై పడదు, విమానాలు లేదా పక్షులు ఈ ఆలయం పైనుంచి ఎగరవు. వంటశాలలో 7 కుండలు ఒకదానిపై ఒకటి ఉంచితే పై కుండలోని ఆహారమే ముందు ఉడుకుతుంది.",
        "curiosity_score": 10,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "పూరి జగన్నాథుని ఆలయంపై పతాకం గాలికి వ్యతిరేక దిశలో ఎందుకు ఎగురుతుంది?",
            "ఈ ప్రపంచంలో నీడ పడని ఏకైక మహా దేవాలయం ఇదేనా?",
            "7 కుండలు ఒకదానిపై ఒకటి పెడితే పై కుండలోని అన్నమే ముందు ఎలా ఉడుకుతుంది?"
        ]
    },
    {
        "id": "tirumala-balaji-roar",
        "title": "తిరుమల శ్రీవారి విగ్రహం వెనుక సముద్ర ఘోష & ఆరని అఖండ దీపాలు",
        "english_title": "Tirumala: The Roar of Ocean Waves Behind Balaji Idol",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "శ్రీ వేంకటేశ్వర స్వామి (Lord Venkateswara)",
        "source": "తిరుమల క్షేత్ర చరిత్ర",
        "summary": "తిరుమల ఆనంద నిలయంలోని శ్రీవారి విగ్రహం వెనుక చెవి ఆనించి వింటే స్వచ్ఛమైన సముద్రపు అలల శబ్దం వినిపిస్తుంది. గర్భగుడిలోని దీపాలు శతాబ్దాలుగా కొండెక్కకుండా వెలుగుతూనే ఉన్నాయి. స్వామివారి వీపుపై పచ్చ కర్పూరం పెట్టినా శిల పగలకపోవడం సైన్స్ పరిశోధనల్లో తేలని రహస్యం.",
        "curiosity_score": 9,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "సముద్రానికి 3000 అడుగుల ఎత్తున ఉన్న తిరుమల విగ్రహం వెనుక సముద్ర ఘోష ఎలా వస్తుంది?",
            "శతాబ్దాలుగా కొండెక్కని ఆనంద నిలయ దీపాల అద్భుతం!",
            "శ్రీవారి వీపుపై నిత్యం పచ్చి కర్పూరం పెట్టినా శిలా విగ్రహం ఎందుకు పగలదు?"
        ]
    },
    {
        "id": "yaganti-growing-nandi",
        "title": "యాగంటి క్షేత్రంలో ఏటా పరిమాణం పెరిగే నందీశ్వరుడి విగ్రహ రహస్యం",
        "english_title": "The Mysterious Growing Nandi of Yaganti",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "ఉమా మహేశ్వరుడు (Nandi & Shiva)",
        "source": "పురాణ క్షేత్రాలు",
        "summary": "కర్నూలు జిల్లా యాగంటిలోని నందీశ్వరుడి విగ్రహం ప్రతి 20 ఏళ్లకు ఒక అంగుళం చొప్పున పెరుగుతోందని జియోలాజికల్ సర్వే ఆఫ్ ఇండియా ధ్రువీకరించింది. దీని చుట్టూ ఉన్న స్తంభాలను ఇప్పటికే తొలగించాల్సి వచ్చింది. కలియుగాంతంలో ఈ నంది ప్రాణం పోసుకుని రంకె వేస్తుందని కాలజ్ఞానంలో ఉంది.",
        "curiosity_score": 10,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "ఈ నంది విగ్రహం నిజంగానే ఏటా పెరుగుతోందా? జియోలాజికల్ సర్వే ఏం చెబుతోంది?",
            "కలియుగాంతంలో ప్రాణం పోసుకుని లేచే నంది ఇదేనా?",
            "శాస్త్రవేత్తలనే విస్మయానికి గురిచేసిన యాగంటి నంది విగ్రహ రహస్యం!"
        ]
    },
    {
        "id": "ellora-kailash-carving",
        "title": "ఎల్లోరా కైలాస దేవాలయం: పైనుంచి క్రిందికి ఒకే రాతిలో చెక్కిన విస్మయం",
        "english_title": "Ellora Kailash Temple: Carved Top to Bottom from a Mountain",
        "category": "దేవాలయ అద్భుతాలు (Temple Marvels)",
        "category_key": "temples",
        "deity": "పరమశివుడు (Lord Shiva)",
        "source": "ప్రాచీన భారతీయ శిల్పకళ",
        "summary": "ఆధునిక క్రేన్లు, మెషీన్లు లేని కాలంలో 4 లక్షల టన్నుల ఏకశిలా పర్వతాన్ని కేవలం ఉలి, సుత్తితో పైనుంచి క్రిందికి చెక్కి నిర్మించిన ఏకైక అద్భుతం. ఔరంగజేబు వేలమంది సైనికులతో 3 సంవత్సరాలు ప్రయత్నించినా ఈ ఆలయాన్ని కూల్చలేకపోయాడు.",
        "curiosity_score": 9,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "పైనుంచి క్రిందికి కొండను తొలిచి చెక్కిన ఈ ప్రపంచపు ఏకైక అద్భుతం గురించి తెలుసా?",
            "ఔరంగజేబు 3 సంవత్సరాలు శ్రమించినా ఈ గుడిని ఎందుకు కూల్చలేకపోయాడు?",
            "ఆధునిక ఇంజనీరింగ్ కూడా చేయలేని ప్రాచీన భారతీయ నిర్మాణ వైభవం!"
        ]
    },
    {
        "id": "krishna-govardhana",
        "title": "చిటికెన వేలిపై గోవర్ధన గిరిని ఎత్తిన శ్రీకృష్ణ లీల",
        "english_title": "Krishna Lifting Govardhana Hill on His Little Finger",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "శ్రీకృష్ణుడు (Lord Krishna)",
        "source": "శ్రీమద్భాగవతం",
        "summary": "ఇంద్రుడి అహంకారాన్ని అణచడానికి మరియు కుంభవృష్టి వర్షం నుండి గోపాలురను, గోవులను కాపాడటానికి కేవలం తన ఎడమచేతి చిటికెన వేలిపై 7 రాత్రులు, 7 పగళ్ళు గోవర్ధన పర్వతాన్ని గొడుగులా ఎత్తి పట్టుకున్న బాలకృష్ణుడి అద్భుత లీల.",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "శ్రీకృష్ణుడు గోవర్ధన పర్వతాన్ని కేవలం చిటికెన వేలిపైనే ఎందుకు ఎత్తాడు?",
            "7 రోజుల పాటు ఆహారం లేకుండా ప్రజలను కాపాడిన కృష్ణుడి లీల!",
            "దేవతల రాజు ఇంద్రుడి గర్వాన్ని శ్రీకృష్ణుడు ఎలా అణచివేశాడు?"
        ]
    },
    {
        "id": "karna-kavacha-kundala",
        "title": "కర్ణుడి అజేయ కవచ కుండలాల దాన వైభవం",
        "english_title": "Karna's Supreme Sacrifice of His Kavacha Kundalas",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "కర్ణుడు & సూర్యుడు (Karna & Surya)",
        "source": "మహాభారతం",
        "summary": "తన ప్రాణాలను కాపాడే సహజ కవచ కుండలాలను ఇంద్రుడు బ్రాహ్మణ వేషంలో వచ్చి అడిగితే, మృత్యువు తప్పదని తెలిసి కూడా శరీరం నుండి కోసి రక్తం కారుతుండగా దానమిచ్చిన దానవీర శూర కర్ణుడి త్యాగ నిరతి.",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "తన ప్రాణమే పోతుందని తెలిసి కూడా కర్ణుడు కవచ కుండలాలను ఎందుకు దానం చేశాడు?",
            "సూర్యభగవానుడు ముందే హెచ్చరించినా కర్ణుడు వెనకడుగు ఎందుకు వేయలేదు?",
            "మహాభారతంలో అత్యంత భావోద్వేగభరితమైన దాన ఘట్టం ఇది!"
        ]
    },
    {
        "id": "narasimha-pillar-manifestation",
        "title": "రాతి స్తంభం చీల్చుకుని ఉద్భవించిన నరసింహ స్వామి ఉగ్రరూపం",
        "english_title": "Lord Narasimha Manifesting from the Stone Pillar",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "శ్రీ నరసింహ స్వామి (Lord Narasimha)",
        "source": "శ్రీమద్భాగవతం",
        "summary": "హిరణ్యకశిపుడి అసాధ్యమైన వరాలను ఛేదిస్తూ... మనిషి కాక మృగము కాక, గాలిలో కాక నేలపై కాక, ఇంట్లో కాక బయట కాక గడపపై, రాత్రి కాక పగలు కాక సంధ్యా సమయంలో ఉద్భవించి లోకాలను రక్షించిన దివ్య అవతారం.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "హిరణ్యకశిపుడి చావు లేని బ్రహ్మ వరాన్ని నరసింహ స్వామి ఎలా ఛేదించాడు?",
            "చిన్నారి ప్రహ్లాదుడి ఒక్క మాట కోసం రాతి స్తంభంలోంచి దేవుడు ఎలా ప్రత్యక్షమయ్యాడు?",
            "సాయంత్రం సంధ్యా సమయంలో గడపపైనే ఎందుకు సంహరించాల్సి వచ్చింది?"
        ]
    },
    {
        "id": "science-pranayama-brain",
        "title": "ప్రాణాయామం & ఓంకారం జపించినప్పుడు మెదడులో ఏం జరుగుతుంది?",
        "english_title": "What Happens to the Human Brain During Pranayama & Om Chanting",
        "category": "సంప్రదాయ విజ్ఞానం (Tradition Science)",
        "category_key": "science_tradition",
        "deity": "ప్రాచీన యోగ విజ్ఞానం (Patanjali Yoga)",
        "source": "న్యూరోసైన్స్ & యోగ సాధన",
        "summary": "ఓంకార నాదం చేసినప్పుడు మెదడులోని వాగస్ నెర్వ్ యాక్టివేట్ అయి కార్టిసాల్ స్ట్రెస్ హార్మోన్లు 60% తగ్గుతాయి. ఆల్ఫా బ్రెయిన్ వేవ్స్ పెరిగి అంతర్గత శాంతి, ఏకాగ్రత అద్భుతంగా మెరుగుపడతాయి.",
        "curiosity_score": 10,
        "assigned_style": "cinematic-what-if",
        "hook_angles": [
            "ఓంకారం ఉచ్చరించినప్పుడు మానవ మెదడులో జరిగే ఆ అద్భుత రసాయన మార్పులేంటి?",
            "ప్రాణాయామం వల్ల స్ట్రెస్ హార్మోన్లు క్షణాల్లో ఎలా మాయమవుతాయి?",
            "పతంజలి మహర్షి వేల ఏళ్ల క్రితమే కనిపెట్టిన మెడికల్ న్యూరోసైన్స్!"
        ]
    },
    {
        "id": "science-peepal-pradakshina",
        "title": "రావి చెట్టు చుట్టూ ప్రదక్షిణలు చేయడం వెనుక ఉన్న అసలు సైన్స్ ఏమిటి?",
        "english_title": "The Scientific Secret of Peepal Tree Pradakshina",
        "category": "సంప్రదాయ విజ్ఞానం (Tradition Science)",
        "category_key": "science_tradition",
        "deity": "వృక్ష రాజః (Peepal Tree)",
        "source": "ఆయుర్వేద విజ్ఞానం",
        "summary": "రావి చెట్టు 24 గంటలూ ఆక్సిజన్ విడుదల చేసే అరుదైన వృక్షం. ఉదయాన్నే సూర్యోదయ సమయంలో రావి చెట్టు చుట్టూ ప్రదక్షిణలు చేయడం వల్ల విడుదలయ్యే ఓజోన్ గాలి మహిళల హార్మోన్ల సమతుల్యతకు, రోగనిరోధక శక్తికి అత్యంత మేలు చేస్తుంది.",
        "curiosity_score": 9,
        "assigned_style": "cinematic-what-if",
        "hook_angles": [
            "పెద్దలు ఉదయాన్నే రావి చెట్టు చుట్టూ 108 ప్రదక్షిణలు ఎందుకు చేయమన్నారో తెలుసా?",
            "మన పూర్వీకులు రావి చెట్టు పూజ వెనుక దాచిన అద్భుత సైన్స్ ఇది!",
            "24 గంటలూ ఆక్సిజన్ ఇచ్చే చెట్టు కింద నడిస్తే శరీరంలో ఏం మార్పులు వస్తాయి?"
        ]
    },
    {
        "id": "turmeric-threshold-science",
        "title": "గడపకు పసుపు, గుమ్మానికి మామిడి తోరణాలు ఎందుకు కడతారు?",
        "english_title": "Why Turmeric at Threshold & Mango Leaves at Door",
        "category": "సంప్రదాయ విజ్ఞానం (Tradition Science)",
        "category_key": "science_tradition",
        "deity": "గృహ లక్ష్మి (Indian Traditions)",
        "source": "ప్రాచీన గృహ వైద్యం",
        "summary": "పసుపులో శక్తివంతమైన కర్కుమిన్, క్రిమినాశక గుణాలు ఉన్నాయి. పూర్వకాలంలో విషసర్పాలు, హానికర క్రిమికీటకాలు ఇంట్లోకి రాకుండా సహజ యాంటీ-సెప్టిక్ రక్షణగా గడపకు పసుపు రాసేవారు. మామిడి ఆకులు గాలిలోని కార్బన్ డయాక్సైడ్‌ను పీల్చి స్వచ్ఛమైన ఆక్సిజన్ ఇస్తాయి.",
        "curiosity_score": 9,
        "assigned_style": "cinematic-what-if",
        "hook_angles": [
            "ప్రతి శుక్రవారం గడపకు పసుపు ఎందుకు రాస్తారో అసలు సైన్స్ తెలుసా?",
            "మన పూర్వీకులు కనిపెట్టిన ప్రాచీన సహజ శానిటైజర్ టెక్నాలజీ!",
            "గుమ్మానికి మామిడి తోరణాలు కడితే ఇంట్లోకి నెగెటివ్ ఎనర్జీ రాదా?"
        ]
    },
    {
        "id": "copper-vessel-water",
        "title": "రాత్రంతా రాగి పాత్రలో పెట్టిన నీరు ఉదయాన్నే తాగితే ఏమవుతుంది?",
        "english_title": "What Happens When You Drink Water Stored in Copper Vessel",
        "category": "సంప్రదాయ విజ్ఞానం (Tradition Science)",
        "category_key": "science_tradition",
        "deity": "ఆయుర్వేద జీవన విధానం",
        "source": "తామ్ర జల శాస్త్రం",
        "summary": "రాగి పాత్రలో 8 గంటలు నిల్వ ఉంచిన నీటిలో ఆలిగోడైనమిక్ ప్రభావం వల్ల నీటిలోని హానికర బ్యాక్టీరియా నశిస్తుంది. ఈ తామ్ర జలం శరీరంలోని వాత, పిత్త, కఫ దోషాలను సమతుల్యం చేసి, జీర్ణక్రియను వేగవంతం చేస్తుంది.",
        "curiosity_score": 9,
        "assigned_style": "cinematic-what-if",
        "hook_angles": [
            "రాత్రంతా రాగి పాత్రలో పెట్టిన నీరు ఉదయాన్నే తాగితే శరీరంలో ఏం మార్పులు వస్తాయి?",
            "ప్రాచీన ఆయుర్వేదంలో తామ్ర జలానికి ఉన్న అద్భుత శక్తులు ఇవే!",
            "ప్లాస్టిక్ బాటిల్స్ వదిలేసి రాగి పాత్రల వైపు ప్రపంచం ఎందుకు చూస్తోంది?"
        ]
    },
    {
        "id": "tenali-rama-cat",
        "title": "తెనాలి రామకృష్ణుడి పిల్లికి పాలు తాగించే చమత్కార కథ",
        "english_title": "Tenali Rama and the Milk-Drinking Cat Wisdom",
        "category": "చారిత్రక చమత్కారాలు (Historical Legends)",
        "category_key": "legends",
        "deity": "తెనాలి రామకృష్ణుడు",
        "source": "రాయల కాలపు హాస్య కథలు",
        "summary": "శ్రీకృష్ణదేవరాయలు ఎలుకలను అరికట్టడానికి ప్రజలకు పిల్లులను పంచి, వాటికి పాలు పోయాలని ఆజ్ఞాపించినప్పుడు... తెనాలి రాముడు వేడి వేడి పాలు పోసి పిల్లిని పాలకు దూరంగా ఉంచి, ఆ పాలను తన బిడ్డలకు తాగించి ఎలా సమయస్ఫూర్తి చాటుకున్నాడో తెలిపే ప్రసిద్ధ కథ.",
        "curiosity_score": 8,
        "assigned_style": "engineering-explainer",
        "hook_angles": [
            "తెనాలి రాముడు రాయలవారిని తన తెలివితో ఎలా ఆశ్చర్యపరిచాడు?",
            "పిల్లికి పాలు తాగించమంటే తెనాలి రాముడు చేసిన ఆ చిలిపి పనేంటి?",
            "తెలుగు హాస్యంలో తెనాలి రామకృష్ణుడి సమయస్ఫూర్తి ఎందుకు అద్భుతం?"
        ]
    },
    # --- చందమామ & తెలుగు కథల పుస్తకాలు (Telugu Storybooks & Folklore) ---
    {
        "id": "chandamama-smart-thief-judgment",
        "title": "చందమామ కథ: దొంగను పట్టిన తెలివైన తీర్పు",
        "english_title": "Chandamama: The Clever Judgment that Trapped the Thief",
        "category": "చందమామ కథలు (Telugu Storybooks)",
        "category_key": "storybooks",
        "deity": "తెలుగు జానపద కథ",
        "source": "చందమామ కథా భాండాగారం",
        "summary": "ఒక ధనవంతుడి ఇంట్లో వజ్రాల హారం మాయమైతే... అనుమానితులందరి చేతికి సమానమైన పొడుగున్న మంత్రపు కర్రలను ఇచ్చి, 'దొంగ చేతిలోని కర్ర రాత్రికి ఒక అంగుళం పెరుగుతుంది' అని న్యాయాధికారి చెప్పినప్పుడు... అసలైన దొంగ భయంతో తన కర్రను ఒక అంగుళం కత్తిరించి ఎలా పట్టుబడ్డాడో తెలిపే చందమామ క్లాసిక్ కథ.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "మంత్రపు కర్రలతో దొంగను క్షణాల్లో ఎలా పట్టించారో తెలుసా?",
            "దొంగ తనంతట తానే దొరికిపోయేలా చేసిన అద్భుతమైన చందమామ తీర్పు!",
            "చందమామ కథల్లోని ఈ తెలివైన న్యాయం వింటే ఎవరైనా ఆశ్చర్యపోవాల్సిందే!"
        ]
    },
    {
        "id": "vikram-betal-three-brothers",
        "title": "విక్రమార్క బేతాళ కథ: ముగ్గురు సున్నిత సోదరుల వింతైన పరీక్ష",
        "english_title": "Vikram Betal: The Test of the Three Hyper-Sensitive Brothers",
        "category": "బేతాళ కథలు (Riddle Tales)",
        "category_key": "storybooks",
        "deity": "విక్రమార్కుడు & బేతాళుడు",
        "source": "బేతాళ పంచవింశతి",
        "summary": "ఒకరు అన్నంలో శవం వాసనను పసిగట్టే ఘ్రాణశక్తి, రెండవవాడు ఆవు దూడ మేక పాలు తాగి పెరిగిందని చెప్పే రుచిజ్ఞానం, మూడవవాడు ఏడు పరుపుల కింద ఉన్న వెంట్రుకను వీపుపై గాయంతో గుర్తించే స్పర్శజ్ఞానం గల ముగ్గురిలో... నిజమైన సున్నిత జ్ఞాని ఎవరు? బేతాళుడి క్లిష్టమైన చిక్కుముడి ప్రశ్న.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "ఏడు పరుపుల కింద ఉన్న ఒక్క వెంట్రుక తగిలి వీపుపై రక్తపు గాయమైన మనిషి కథ!",
            "ఈ ముగ్గురు సోదరులలో నిజమైన మహా జ్ఞాని ఎవరు? బేతాళుడి చిక్కు ప్రశ్న!",
            "విక్రమార్కుడిని సైతం నిశ్చేష్టుడిని చేసిన విచిత్రమైన బేతాళ రిడిల్!"
        ]
    },
    {
        "id": "tenali-rama-well-digging",
        "title": "తెనాలి రామకృష్ణుడు: దొంగలతోనే పెరటి బావి తవ్వించిన చమత్కారం",
        "english_title": "Tenali Rama: Tricking Thieves into Watering the Garden",
        "category": "తెనాలి రామకృష్ణుడి కథలు (Tenali Rama)",
        "category_key": "storybooks",
        "deity": "తెనాలి రామకృష్ణుడు",
        "source": "శ్రీకృష్ణదేవరాయల ఆస్థాన కథలు",
        "summary": "తన ఇంటిని దోచుకోవడానికి వచ్చిన దొంగలను కనిపెట్టిన తెనాలి రాముడు... భార్యతో గట్టిగా మాట్లాడుతూ నగలు, నాణేల పెట్టెను బావిలో దాస్తున్నట్లు నాటకమాడి, పెద్ద రాతి పెట్టెను బావిలో పడేస్తాడు. దొంగలు రాత్రంతా బావిలోని నీటిని తోడి పెరటి తోట మొత్తానికి నీరు పారించి చివరకు ఒట్టి పెట్టె చూసి తెల్లబోయిన హాస్యభరిత కథ.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "తన ఇంటికి వచ్చిన దొంగలతోనే తోట మొత్తం తవ్వించిన తెనాలి రాముడి తెలివి!",
            "దొంగలు రాత్రంతా బావి నీళ్లు తోడేలా తెనాలి రాముడు ఆడిన నాటకమేంటి?",
            "శ్రీకృష్ణదేవరాయలనే కడుపుబ్బా నవ్వించిన తెనాలి రామకృష్ణుడి సమయస్ఫూర్తి!"
        ]
    },
    {
        "id": "maryada-ramanna-true-mother",
        "title": "మర్యాద రామన్న తీర్పు: అసలైన కన్నతల్లి ఎవరు?",
        "english_title": "Maryada Ramanna: Who is the Real Biological Mother?",
        "category": "మర్యాద రామన్న తీర్పులు (Justice Legends)",
        "category_key": "storybooks",
        "deity": "మర్యాద రామన్న",
        "source": "తెలుగు జానపద న్యాయ కథలు",
        "summary": "ఒకే పసిబిడ్డ కోసం ఇద్దరు స్త్రీలు పోటీపడినప్పుడు... 'బిడ్డను చెరిసగం కోసి ఇద్దరికీ సమానంగా పంచండి' అని మర్యాద రామన్న కత్తి దూయమన్నప్పుడు, 'వద్దు బిడ్డను ఆమే తీసుకోనీయండి, నా బిడ్డ ప్రాణాలతో బతికుంటే చాలు' అని ఏడ్చిన నిజమైన తల్లి ప్రేమను రామన్న ఎలా కనిపెట్టాడో తెలిపే గుండెను హత్తుకునే తీర్పు.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "బిడ్డను రెండు ముక్కలుగా కోయమని న్యాయాధికారి ఎందుకు ఆజ్ఞాపించాడు?",
            "మర్యాద రామన్న కనిపెట్టిన ఆ నిజమైన కన్నతల్లి ప్రేమ రహస్యం!",
            "తెలుగు కథల్లో ఇప్పటికీ మర్చిపోలేని అద్భుతమైన తీర్పు ఇది!"
        ]
    },
    {
        "id": "panchatantra-rabbit-lion-reflection",
        "title": "పంచతంత్రం: సింహాన్ని బావిలోకి దూకించిన చిన్నారి కుందేలు",
        "english_title": "Panchatantra: The Tiny Rabbit that Outsmarted the Lion in a Well",
        "category": "పంచతంత్ర కథలు (Panchatantra)",
        "category_key": "storybooks",
        "deity": "విష్ణుశర్మ పంచతంత్రం",
        "source": "పంచతంత్ర నీతి కథలు",
        "summary": "అడవిలోని జంతువులను వేటాడి చంపే క్రూరమైన సింహాన్ని... ఒక చిన్న కుందేలు బావి వద్దకు తీసుకెళ్లి, నీటిలో కనిపించే స్వంత ప్రతిబింబాన్ని చూపి 'ఇదిగో నీకంటే బలమైన మరో సింహం ఇక్కడే దాగుంది' అని రెచ్చగొట్టి, సింహం బావిలోకి దూకి చనిపోయేలా చేసిన బుద్ధిబల గాథ.",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "ఒక చిన్న కుందేలు అడవికే రాజైన సింహాన్ని ఎలా చంపగలిగింది?",
            "కండబలం కంటే బుద్ధిబలమే గొప్పదని నిరూపించిన పంచతంత్ర కథ!",
            "బావిలో స్వంత నీడను చూసి మోసపోయిన క్రూర మృగరాజు!"
        ]
    },
    {
        "id": "chandamama-three-magic-gifts",
        "title": "చందమామ కథ: ముగ్గురు సోదరులు & మూడు మాయా వస్తువులు",
        "english_title": "Chandamama: Three Brothers and Three Magical Artifacts",
        "category": "చందమామ కథలు (Telugu Storybooks)",
        "category_key": "storybooks",
        "deity": "తెలుగు జానపద కథ",
        "source": "చందమామ అద్భుత కథలు",
        "summary": "దూరతీరాల్లో ఏం జరుగుతుందో చూపే మాయా అద్దం, క్షణాల్లో ఎక్కడికైనా ఎగిరిపోయే మాయా తివాచీ, చనిపోయిన వారిని బతికించే మాయా సంజీవని పండు పొందిన ముగ్గురు సోదరులు... వ్యాధితో ఉన్న రాకుమారిని ఎలా కాపాడారు? వారిలో రాకుమారిని పెళ్లి చేసుకోవడానికి నిజమైన అర్హుడు ఎవరు?",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "మాయా అద్దం, ఎగిరే తివాచీ, సంజీవని పండు... రాకుమారిని కాపాడింది ఎవరు?",
            "ఈ ముగ్గురు సోదరులలో రాకుమారిని పెళ్లి చేసుకోవడానికి ఎవరికి ఎక్కువ హక్కుంది?",
            "చందమామ పాత సంచికల్లో వచ్చిన అత్యంత ప్రజాదరణ పొందిన రిడిల్ కథ!"
        ]
    },
    # --- హిందూ పురాణ కథలు (Hindu Mythology & Epics) ---
    {
        "id": "hanuman-sanjeevani-mountain",
        "title": "లక్ష్మణుడి ప్రాణం కోసం సంజీవని పర్వతాన్నే పెకలించిన హనుమంతుడు",
        "english_title": "Hanuman Lifting Mount Dronagiri for Sanjeevani Herb",
        "category": "రామాయణ మహత్యం (Ramayana)",
        "category_key": "epics",
        "deity": "శ్రీ ఆంజనేయ స్వామి (Lord Hanuman)",
        "source": "వాల్మీకి రామాయణం - యుద్ధకాండ",
        "summary": "ఇంద్రజిత్తు ప్రయోగించిన శక్తి ఆయుధానికి లక్ష్మణుడు మూర్ఛిల్లినప్పుడు... సూర్యోదయానికి ముందే సంజీవని మూలికను తీసుకురావాలని సుషేణుడు చెబితే, హిమాలయాల్లో మూలికను గుర్తించలేక ఏకంగా ద్రోణగిరి పర్వతాన్నే చేతిపై ఎత్తుకుని సముద్రాలు దాటి తీసుకొచ్చిన భక్త హనుమాన్ అమోఘ పరాక్రమం.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "ఒక్క మూలిక కోసం ఏకంగా కొండనే ఎత్తుకొచ్చిన హనుమంతుడి కథ!",
            "సూర్యోదయానికి ముందే హిమాలయాల నుంచి లంకకు పర్వతాన్ని ఎలా మోసుకొచ్చాడు?",
            "రామాయణంలో లక్ష్మణుడి ప్రాణాన్ని కాపాడిన ఆ దివ్య మూలిక ఏంటి?"
        ]
    },
    {
        "id": "ganesha-world-race-mango",
        "title": "మూడు లోకాల పందెంలో తల్లిదండ్రుల చుట్టూ 3 అడుగులతో గెలిచిన గణపతి",
        "english_title": "Ganesha Winning the Cosmic Fruit by Circling Parents",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "శ్రీ మహాగణపతి (Lord Ganesha)",
        "source": "స్కాంద పురాణం / శివ పురాణం",
        "summary": "నారదుడు తెచ్చిన జ్ఞాన ఫలం కోసం కుమారస్వామి తన నెమలి వాహనంపై సమస్త బ్రహ్మాండాన్ని చుట్టిరావడానికి బయలుదేరితే... బొజ్జ గణపయ్య మాత్రం 'సమస్త లోకాలు తల్లిదండ్రుల పాదాల చెంతనే ఉన్నాయి' అని శివపార్వతుల చుట్టూ మూడు ప్రదక్షిణలు చేసి పందెంలో విజేతగా నిలిచిన సనాతన ధర్మ విజ్ఞాన కథ.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "సమస్త విశ్వాన్ని చుట్టిరావాల్సిన పందెంలో వినాయకుడు మూడు అడుగులతో ఎలా గెలిచాడు?",
            "తల్లిదండ్రులకు ప్రదక్షిణ చేస్తే సమస్త బ్రహ్మాండం చుట్టినట్లేనా?",
            "కుమారస్వామి కంటే ముందే జ్ఞాన ఫలాన్ని గణపతి ఎలా పొందాడు?"
        ]
    },
    {
        "id": "ganesha-kubera-feast",
        "title": "కుబేరుడి సమస్త సంపదను, ఆహారాన్ని క్షణాల్లో ఆరగించిన బాల గణపతి",
        "english_title": "Little Ganesha Devouring Wealth God Kubera's Entire Feast",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "బాల గణపతి & కుబేరుడు",
        "source": "గణేశ పురాణం",
        "summary": "తానే లోకంలో అత్యంత ధనవంతుడిననే గర్వంతో కుబేరుడు కైలాసానికి వెళ్లి విందు ఆహ్వానం పలికితే... పరమశివుడు బాల గణపతిని పంపుతాడు. కుబేరుడి బంగారు నగరం అలకాపురిలోని ఆహారమంతా తినేసి, పాత్రలను, బంగారు వస్తువులను కూడా నమలడం ప్రారంభించిన గణపతి ఆకలికి కుబేరుడి గర్వం ఎలా పటాపంచలైందో తెలిపే అద్భుత లీల.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "ధనదేవత కుబేరుడి సంపద మొత్తాన్ని గణపతి ఒక్క పూటలో ఎలా ఖాళీ చేశాడు?",
            "కుబేరుడి అహంకారాన్ని దించడానికి పరమశివుడు వేసిన ప్లాన్ ఏంటి?",
            "చివరకు ఒక్క గుప్పెడు పేలాల ముద్దతో గణపతి ఆకలి ఎలా తీరింది?"
        ]
    },
    {
        "id": "bhagavatgita-vishwaroopa-darshanam",
        "title": "కురుక్షేత్రంలో అర్జునుడికి శ్రీకృష్ణుడు చూపిన భయానక విశ్వరూపం",
        "english_title": "The Terrifying Cosmic Vishwaroopa Revealed to Arjuna",
        "category": "మహాభారత తత్త్వం (Mahabharata)",
        "category_key": "epics",
        "deity": "శ్రీకృష్ణ పరమాత్మ (Cosmic Form)",
        "source": "శ్రీమద్భగవద్గీత - 11వ అధ్యాయం",
        "summary": "యుద్ధరంగంలో బంధుప్రీతితో గాండీవాన్ని జారవిడిచిన అర్జునుడికి... వేల కొద్దీ సూర్యుల తేజస్సుతో, అనంతమైన ముఖాలు, కళ్లు, సమస్త లోకాలు తనలోనే లయమవుతున్న భయంకర కాలస్వరూపాన్ని చూపించి 'వీరందరినీ కాలమే ముందే సంహరించింది, నువ్వు కేవలం నిమిత్తమాత్రుడివి' అని కర్తవ్యబోధ చేసిన దివ్య ఘట్టం.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "వేయి సూర్యుల కాంతితో కృష్ణుడు చూపిన ఆ భయంకర విశ్వరూపం ఎలా ఉంది?",
            "అర్జునుడు భయంతో వణికిపోయి చేతులు జోడించి వేడుకోవడానికి కారణం ఏంటి?",
            "భగవద్గీతలో మానవ ఊహకందని అత్యంత భారీ కాస్మిక్ విజన్ ఇది!"
        ]
    },
    {
        "id": "bhagiratha-ganga-descent",
        "title": "ఆకాశ గంగను భూమికి దించిన భగీరథుడి అపర తపస్సు & శివుడి జటాఝూటం",
        "english_title": "Bhagiratha Bringing Down Ganga & Shiva Taming the Torrent",
        "category": "పురాణ గాథలు (Puranic Feats)",
        "category_key": "epics",
        "deity": "పరమశివుడు & గంగాదేవి",
        "source": "వాల్మీకి రామాయణం - బాలకాండ",
        "summary": "తన పూర్వీకులైన 60 వేల మంది సగర పుత్రులకు మోక్షం ప్రసాదించడానికి... ఆకాశంలో ఉధృతంగా ప్రవహించే గంగను భూమికి తీసుకురావడానికి భగీరథుడు ఘోర తపస్సు చేశాడు. ఆ ఉధృతికి భూమి బద్దలవుతుందని పరమశివుడు తన జటాఝూటంలో గంగను బంధించి ఒక చిన్న పాయలా భూమిపైకి వదిలిన అద్భుత పురాణ గాథ.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "భూమి బద్దలయ్యే వేగంతో దూసుకొచ్చిన గంగను శివుడు తన జుట్టులో ఎలా బంధించాడు?",
            "పూర్వీకుల మోక్షం కోసం భగీరథుడు చేసిన ఆ అసాధ్యమైన ప్రయత్నమేంటి?",
            "'భగీరథ ప్రయత్నం' అనే నానుడి వెనుక ఉన్న అసలు పురాణ చరిత్ర ఇది!"
        ]
    },
    {
        "id": "abhimanyu-padmavyuham",
        "title": "అభిమన్యుడి పద్మవ్యూహ భేదనం: 16 ఏళ్ల వీరుడి అజేయ పోరాటం",
        "english_title": "Abhimanyu's Valour in the Deadly Chakravyuha",
        "category": "మహాభారత పరాక్రమం (Mahabharata)",
        "category_key": "epics",
        "deity": "వీర అభిమన్యుడు (Abhimanyu)",
        "source": "మహాభారతం - ద్రోణ పర్వం",
        "summary": "తల్లి గర్భంలో ఉండగానే పద్మవ్యూహంలోకి ప్రవేశించే విద్యను మాత్రమే విని, బయటకు వచ్చే మార్గం తెలియకపోయినా... పాండవుల గౌరవం కోసం ఒంటరిగా ద్రోణాచార్యుడు, కర్ణుడు, దుర్యోధనుడు మొదలైన మహారథులందరినీ గడగడలాడించి, రథ చక్రంతో చివరి శ్వాస వరకు పోరాడిన 16 ఏళ్ల బాలవీరుడి అమర గాథ.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "పద్మవ్యూహంలోకి వెళ్లడం మాత్రమే తెలిసిన 16 ఏళ్ల బాలుడు లోపలికి ఎందుకు వెళ్లాడు?",
            "మహామహా యోధులందరూ కలిసి ఒంటరిగా ఉన్న అభిమన్యుడిని ఎందుకు చంపాల్సి వచ్చింది?",
            "మహాభారతంలో కన్నీళ్లు పెట్టించే అత్యంత వీరోచిత పోరాటం ఇది!"
        ]
    }
]



# ==============================================================================
# CURATED ANCIENT CIVIL ENGINEERING & STRUCTURAL BREAKDOWN CATALOG (ENGLISH)
# Format: The Evolutionary Engineering Loop
# Primitive Idea -> Physics Flaw -> Stone Upgrade -> Tensile Failure ->
# Arch/Physics Breakthrough -> Scaffolding/Concrete Hack -> Real Monument -> Outro
# ==============================================================================
ENGLISH_CONCEPT_CATALOG = [
    {
        "id": "doorway-event-boundary-memory",
        "title": "Why You Walk Into a Room and Forget What You Came For",
        "what_if_title": "What If Every Doorway Made You Forget?",
        "category": "Everyday Psychology",
        "topic_lane": "psychology",
        "location": "A familiar room-to-room transition",
        "map_region": "One continuous home shown as linked event contexts",
        "source": "Quarterly Journal of Experimental Psychology; Yale Perception and Cognition Laboratory",
        "references": [
            "https://pubmed.ncbi.nlm.nih.gov/21563019/",
            "https://perception.yale.edu/DoorwayAnticipation/"
        ],
        "summary": "Explain the doorway/event-boundary memory effect with care: some experiments find memory costs around context changes, while results vary by task and study. Show a person carrying an intention across rooms, then make the event boundary visible. Never claim that every doorway erases a memory.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "You walk into the next room—and the reason you came disappears. Why?",
            "The doorway may be acting like a scene cut in your memory.",
            "Your brain updates the scene when you cross a threshold. Does the old goal come with you?"
        ],
        "engineering_steps": {},
    },
    {
        "id": "why-recorded-voice-sounds-strange",
        "title": "Why Your Recorded Voice Sounds Like Someone Else",
        "what_if_title": "What If Every Voice Sounded Like Yours?",
        "category": "Hearing and Perception",
        "topic_lane": "perception",
        "location": "Sound traveling through air and through your own head",
        "map_region": "Ear, skull, and playback speaker cross-section",
        "source": "PLOS ONE; Royal Society Open Science",
        "references": [
            "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0199443",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC9929504/"
        ],
        "summary": "Demonstrate why a person hears their own voice through a mixture of air and body-conducted sound, while a recording is played back through air. Keep the explanation grounded in the studies; do not say bone conduction alone explains every difference in how a recording sounds.",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "That voice memo sounds like you—but why does it feel like a stranger?",
            "You hear your voice two ways. A microphone only catches one of them.",
            "Your skull changes the sound you think everyone else hears."
        ],
        "engineering_steps": {},
    },
    {
        "id": "why-you-cant-tickle-yourself",
        "title": "Why You Can't Tickle Yourself",
        "what_if_title": "What If You Could Tickle Yourself?",
        "category": "Brain and Body",
        "topic_lane": "body-brain",
        "location": "The brain predicting a self-generated touch",
        "map_region": "Movement command, predicted touch, and sensory feedback",
        "source": "Nature Neuroscience; The Journal of Neuroscience",
        "references": [
            "https://www.nature.com/articles/nn1198_635",
            "https://www.jneurosci.org/content/jneuro/40/4/894.full.pdf"
        ],
        "summary": "Show a hand approaching the ribs, then reveal how expected self-generated touch is treated differently from an unexpected touch. Explain the predictive motor signal without claiming one brain area or mechanism fully explains tickling for everyone.",
        "curiosity_score": 9,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "You can touch your own ribs, but you can't surprise yourself into a tickle.",
            "Your brain predicts your hand before it reaches your skin.",
            "Why does the same touch feel different when someone else does it?"
        ],
        "engineering_steps": {},
    },
    {
        "id": "why-songs-get-stuck-in-your-head",
        "title": "Why a Song Gets Stuck in Your Head",
        "what_if_title": "What If Songs Never Left Your Head?",
        "category": "Everyday Psychology",
        "topic_lane": "psychology",
        "location": "Involuntary musical imagery and working memory",
        "map_region": "A short musical loop replaying in a simple mental soundscape",
        "source": "Psychological Review; Sleep journal research",
        "references": [
            "https://doi.org/10.3758/s13423-020-01750-7",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC8641138/"
        ],
        "summary": "Explain earworms as involuntary musical imagery: a fragment can recur without deliberate listening. Show a short loop and plausible triggers such as recent exposure, but do not claim there is one proven cause or a universal cure.",
        "curiosity_score": 8,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "You stopped the song hours ago. So why is the chorus still playing?",
            "A tiny fragment of music can keep returning without you pressing play.",
            "Your brain has a song loop—and the trigger may be smaller than you think."
        ],
        "engineering_steps": {},
    },
    {
        "id": "why-yawns-can-spread",
        "title": "Why Seeing Someone Yawn Can Make You Yawn",
        "what_if_title": "What If Every Yawn Made You Yawn?",
        "category": "Social Behavior",
        "topic_lane": "behavior",
        "location": "A person sees or hears a yawn from someone nearby",
        "map_region": "A simple two-person visual with a sound-to-action link",
        "source": "Proceedings of the Royal Society B; Neuroscience and Biobehavioral Reviews",
        "references": [
            "https://pubmed.ncbi.nlm.nih.gov/35250722/",
            "https://pubmed.ncbi.nlm.nih.gov/28867202/"
        ],
        "summary": "Show that yawns can be socially triggered in laboratory conditions, while keeping the cause and proposed social function open: contagion does not by itself prove empathy. Use current research to distinguish reliable observations from unsettled explanations.",
        "curiosity_score": 8,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "If this yawn made you yawn, what exactly did your brain copy?",
            "A yawn can spread through a screen—but the reason is still debated.",
            "Researchers can trigger contagious yawning in a lab. What does that actually prove?"
        ],
        "engineering_steps": {},
    }
]

ENGLISH_MODERN_ENGINEERING_CATALOG = [
    {
        "id": "roman-arch-aqueduct",
        "title": "How Ancient Romans Actually Built Arch Bridges & Aqueducts",
        "category": "Ancient Civil Engineering",
        "location": "Pont du Gard, Nîmes, France (Roman Empire)",
        "map_region": "Southern Gaul (France) & Roman Mediterranean",
        "source": "Roman Structural Engineering",
        "summary": "To bridge a canyon, laying a flat wooden beam fails when timber bows and washes away in floods. Replacing it with flat stone beams fails because stone snaps under tension in the center. The breakthrough: curving the stones into a semi-circular arch with a locking keystone at the apex, converting tension into pure compression. To build in mid-air, Romans used wooden centering arches, and to set piers underwater, they drove circular cofferdams and poured volcanic pozzolanic concrete that hardens submerged. Stack three tiers, and you have the Pont du Gard standing strong 2,000 years later!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did the Romans build a 160-foot stone aqueduct before modern cranes existed?",
            "If you lay a flat stone beam across two pillars, physics destroys it. Here is how ancient engineers beat gravity.",
            "The genius engineering trick that let ancient Romans pour concrete *underwater*."
        ],
        "engineering_steps": {
            "primitive": "Drop a flat wooden beam across the canyon",
            "flaw": "Timber rots, bows under load, and one flash flood sweeps it away",
            "upgrade1": "Stone pillars with a flat stone lintel beam",
            "flaw2": "Stone has massive compression strength, but snaps easily under tension in the center",
            "breakthrough": "The semi-circular stone arch + central keystone: converts downward load into lateral compression",
            "construction": "Temporary wooden centering scaffolding + watertight wooden cofferdams pumped dry for underwater pozzolanic volcanic concrete",
            "monument": "Pont du Gard Aqueduct (France)",
            "outro": "Congratulations! You now understand the civil engineering behind Roman arch bridges! Which ancient structure should we reverse-engineer next? Comment below!"
        }
    },
    {
        "id": "giza-pyramid-sleds",
        "title": "How Egyptians Built the Great Pyramid: The Friction Physics Secret",
        "category": "Ancient Civil Engineering",
        "location": "Giza Plateau, Egypt (Nile River Valley)",
        "map_region": "Lower Egypt / Nile River Delta",
        "source": "Egyptian Monumental Engineering",
        "summary": "Dragging 2.5-ton limestone blocks across desert sand creates massive sand berms that block the sled. A single straight earthen ramp to the 480-foot peak would need to be a mile long and consume more material than the pyramid itself. The breakthrough: physicists discovered that pouring the exact right amount of water (2-5% volume) on sand stiffens capillary water bridges between sand grains, cutting friction in half! For the upper tiers, internal spiraling ramps inside the masonry core with counterweight sled chutes lifted the blocks into place without mega-ramps.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "A straight ramp to the top of the Great Pyramid would be physically impossible. Here is how they actually built it.",
            "The ancient physics trick that cut the weight of 2-ton pyramid stones in half with water.",
            "How ancient Egyptians lifted 2.3 million stone blocks without wheels or cranes."
        ],
        "engineering_steps": {
            "primitive": "Drag 2.5-ton blocks directly across sand with muscle power",
            "flaw": "Sled blades dig deep into dry sand, creating massive sand berms that halt progress",
            "upgrade1": "Build a giant straight exterior earthen ramp to the summit",
            "flaw2": "A straight ramp would require 3x the volume of the pyramid itself and collapse under its own weight",
            "breakthrough": "Capillary sand lubrication (2-5% water doubles sand stiffness and cuts drag 50%) + internal spiraling ramps with counterweight sled shafts",
            "construction": "River barges during Nile flood season, bronze saws with quartz sand abrasive, and internal limestone counterweights",
            "monument": "The Great Pyramid of Giza (Egypt)",
            "outro": "Congratulations! You now understand the friction physics and internal ramp engineering behind the Great Pyramid! Which ancient marvel should we build next? Let me know in the comments!"
        }
    },
    {
        "id": "pantheon-concrete-dome",
        "title": "How the Pantheon Built the World's Largest Unreinforced Concrete Dome",
        "category": "Ancient Civil Engineering",
        "location": "Rome, Italy",
        "map_region": "Italian Peninsula & Roman Empire",
        "source": "Imperial Roman Vaulting",
        "summary": "If you try to build a 142-foot wide open room with a flat roof, you need a forest of columns every 10 feet. If you cast a massive hemisphere of concrete, the outward lateral thrust will burst the exterior brick walls apart like an overinflated balloon. The Roman solution: step-ring exterior buttresses to clamp the perimeter, graduating the concrete aggregate from heavy travertine at the base down to lightweight volcanic pumice at the top, and leaving an open 30-foot oculus at the peak to eliminate the heaviest central crown entirely!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "Why has the world's largest unreinforced concrete dome not collapsed after 1,900 years?",
            "If you cast a dome out of normal concrete, gravity pushes the walls outward until they burst. Here is the Roman fix.",
            "The secret volcanic recipe behind the Pantheon's floating ceiling."
        ],
        "engineering_steps": {
            "primitive": "Flat timber and tile roof across a giant hall",
            "flaw": "Requires interior support columns every 10 feet, ruining open ceremonial space",
            "upgrade1": "Cast a giant hemispherical solid concrete dome over a circular wall",
            "flaw2": "Massive outward lateral hoop stress pushes outward, cracking and bursting the exterior walls",
            "breakthrough": "Step-ring buttresses on the exterior + density gradation (heavy basalt at base, porous volcanic pumice at crown) + open 30-foot oculus to remove apex weight",
            "construction": "Massive timber centering dome scaffold, sunken coffering to reduce ceiling slab weight, and pozzolana lime mortar",
            "monument": "The Pantheon (Rome, Italy)",
            "outro": "Congratulations! You just reverse-engineered the structural mechanics of the Pantheon! Which ancient structure should we solve next? Comment below!"
        }
    },
    {
        "id": "venice-mud-piles",
        "title": "How Venice Built a Marble City on Mud and Water",
        "category": "Ancient Civil Engineering",
        "location": "Venetian Lagoon, Italy",
        "map_region": "Adriatic Sea & Northern Italy",
        "source": "Venetian Hydro-Engineering",
        "summary": "If you build heavy stone and brick palazzos on a swampy lagoon mudflat, the buildings immediately sink and tilt into the muck. The solution: driving millions of 10-foot sharpened Alder and Oak tree trunks upside-down through the soft mud into the hard 'caranto' clay layer below. Why doesn't the timber rot? Submerged deep beneath the saltwater and mud, there is zero oxygen, meaning wood-eating microbes and fungi cannot survive. The wood petrifies into mineralized stone, topped by water-resistant Istrian limestone foundations that support the floating city of Venice!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How does a city made of heavy marble and brick float on top of ocean mud?",
            "The underwater secret beneath Venice: millions of upside-down petrified tree trunks.",
            "Why doesn't the wood holding up Venice rot after 500 years underwater?"
        ],
        "engineering_steps": {
            "primitive": "Build stone houses directly on the lagoon sandbanks and mudflats",
            "flaw": "Silt cannot bear point loads; foundations sink unevenly, cracking walls and flooding floors",
            "upgrade1": "Drive timber stilts into the soft mud",
            "flaw2": "Tides and waves erode the surface sediment around the stilts",
            "breakthrough": "Drive millions of alder tree trunks through 10 feet of mud down to the compressed 'caranto' hardpan clay layer; zero-oxygen environment prevents rot and petrifies timber",
            "construction": "Double layer of larch planks over pile heads, topped by impermeable Istrian limestone blocks to prevent capillary water rise into brickwork",
            "monument": "Venice Palazzos & St. Mark's Basilica (Italy)",
            "outro": "Congratulations! You now understand the geotechnical engineering that keeps Venice standing on water! What should we explore next? Drop your idea in the comments!"
        }
    },
    {
        "id": "persian-qanats",
        "title": "How Ancient Persians Built Gravity Water Pipelines Under the Desert",
        "category": "Ancient Civil Engineering",
        "location": "Iranian Plateau (Ancient Persia)",
        "map_region": "Middle East & Persian Plateau",
        "source": "Persian Hydraulic Engineering",
        "summary": "In the scorching Iranian desert, surface rivers dry up in summer and open irrigation canals lose 80% of their water to 120°F evaporation. Ancient Persians engineered the Qanat: tapping the 'Mother Well' deep inside the water table at the mountain foothills, then digging an underground sloping tunnel for miles at a precise 0.1% gradient. Water flows purely by gravity with zero evaporation, aerated by vertical shafts every 50 meters that also acted as soil removal access ports, keeping desert cities alive for 3,000 years!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did ancient Persians deliver drinking water across 50 miles of scorching desert?",
            "The 3,000-year-old underground pipeline that runs entirely on gravity with zero pumps.",
            "Why open water canals fail in the desert, and how ancient engineers solved it underground."
        ],
        "engineering_steps": {
            "primitive": "Dig open canals from mountain streams across the desert plains",
            "flaw": "120°F desert heat evaporates most of the water before it reaches the town",
            "upgrade1": "Dig deep vertical wells in the desert floor",
            "flaw2": "Desert water table is too deep and quickly depletes without mountain replenishment",
            "breakthrough": "The Qanat: Tap the mountain aquifer with a Mother Well, then dig a gently sloped (1:1000) subterranean gravity tunnel miles long",
            "construction": "Muqanni miners using oil lamps, plumb lines, and vertical aeration shafts spaced every 50 meters for spoil removal and air intake",
            "monument": "The Persian Qanat Network (UNESCO World Heritage, Iran)",
            "outro": "Congratulations! You just mastered the hydraulic engineering of ancient Persian Qanats! Which ancient feat should we analyze next? Comment below!"
        }
    },
    {
        "id": "incan-earthquake-walls",
        "title": "How the Incas Built Earthquake-Proof Stone Walls Without Mortar",
        "category": "Ancient Civil Engineering",
        "location": "Sacsayhuamán & Machu Picchu, Cusco, Peru",
        "map_region": "Andes Mountains & South America",
        "source": "Inca Megalithic Masonry",
        "summary": "In the seismically active Andes mountains, square brick walls held together by mud mortar shatter and crumble during high-magnitude earthquakes as mortar turns to dust. The Incas engineered interlocking mortar-free dry-stone walls with stones carved with 12 distinct polygon angles and pillow-curved concave/convex joints. When an 8.0 earthquake strikes, the stones slide and 'dance' against each other, absorbing seismic kinetic energy, and then gravity settles them perfectly back into their locked positions!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "Why do modern buildings in Peru collapse during earthquakes while 500-year-old Inca walls survive?",
            "Inca walls don't use a single drop of mortar or cement. Here is why that makes them indestructible.",
            "The secret of the 12-angled stone: seismic energy dissipation in ancient architecture."
        ],
        "engineering_steps": {
            "primitive": "Stack square stone blocks with clay or lime mortar",
            "flaw": "Earthquake shear waves shatter brittle mortar, causing the wall to pancake",
            "upgrade1": "Cut giant megalithic stone boulders and stack them without mortar",
            "flaw2": "Flat horizontal seams slide off each other under horizontal ground acceleration",
            "breakthrough": "Polygonal interlocking joints with beveled pillow faces and matching concave/convex mortise pockets that dissipate seismic energy and resettle",
            "construction": "Hematite hammerstones for precision pecking, inward 3-5 degree wall batter (incline), and trapezoidal doors and windows",
            "monument": "Sacsayhuamán Fortress & Machu Picchu (Peru)",
            "outro": "Congratulations! You now understand the earthquake-proof engineering behind Inca dry-stone masonry! What should we build next? Let me know in the comments!"
        }
    },
    {
        "id": "colosseum-hypogeum-lifts",
        "title": "How the Roman Colosseum's Underground Trapdoor Elevator Network Worked",
        "category": "Ancient Civil Engineering",
        "location": "Rome, Italy",
        "map_region": "Roman Empire / Central Italy",
        "source": "Roman Stage Machinery",
        "summary": "Walking gladiators and wild predators into an arena through perimeter side gates was predictable and quickly bored the 50,000 spectators. Roman engineers excavated a two-story subterranean labyrinth beneath the wooden arena floor called the Hypogeum. They installed 28 vertical wooden elevator shafts powered by manual counterweight capstans and bronze pulleys. Operators hoisted 600-pound lions and gladiators upward, where counterweighted trapdoors snapped open, making scenery and beasts magically appear from under the sand!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did ancient Romans make 600-pound lions magically appear in the middle of the Colosseum?",
            "The secret underground machine room beneath the Colosseum floor: 28 manual elevators.",
            "How ancient engineers operated the world's first special effects arena trapdoor network."
        ],
        "engineering_steps": {
            "primitive": "Lead lions and gladiators through standard perimeter iron gates",
            "flaw": "Crowd sees the entrance coming minutes in advance; zero theatrical suspense",
            "upgrade1": "Dig simple pits with rope ladders under the floor",
            "flaw2": "Manual lifting of caged carnivores is dangerous, slow, and exposes workers to claw attacks",
            "breakthrough": "The Hypogeum: A subterranean network of 28 synchronized capstan winches with counterweighted wooden cage elevators and hinged trapdoors",
            "construction": "Bronze sleeve pulleys, hemp ropes, lead counterweights, and sand-covered hinged trapdoors that opened on cue",
            "monument": "The Roman Colosseum Hypogeum (Rome, Italy)",
            "outro": "Congratulations! You now understand the mechanical stage engineering of the Roman Colosseum! Which ancient machine should we dismantle next? Tell me in the comments!"
        }
    },
    {
        "id": "gothic-flying-buttress",
        "title": "How Gothic Cathedrals Built 150-Foot Glass Walls Without Collapsing",
        "category": "Ancient Civil Engineering",
        "location": "Notre-Dame de Paris & Chartres Cathedral, France",
        "map_region": "Medieval France / Western Europe",
        "source": "Gothic Structural Engineering",
        "summary": "Medieval Romanesque churches had 8-foot thick stone walls with tiny slit windows because cutting large openings caused the massive stone vaulted ceiling to push the walls outward and collapse. Gothic master masons solved this with two genius inventions: pointed arches, which channeled gravity more vertically down into the piers, and Flying Buttresses—exterior stone arched props that reached over the aisles to carry the lateral outward roof thrust outside the building onto giant masonry pillars, allowing walls to become 80% stained glass!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "If you cut giant windows into a 150-foot stone cathedral, the roof collapses. Here is how Gothic architects did it.",
            "The revolutionary stone 'exoskeleton' that let medieval cathedrals replace stone walls with stained glass.",
            "How flying buttresses carry thousands of tons of roof thrust outside the building."
        ],
        "engineering_steps": {
            "primitive": "Thick solid stone walls with barrel vault ceilings (Romanesque style)",
            "flaw": "Dark, damp, cave-like interior; cutting large window openings destroys wall integrity",
            "upgrade1": "Cut large window arches directly into the load-bearing stone walls",
            "flaw2": "Lateral thrust from the heavy stone ceiling pushes the top of the walls outward, collapsing the nave",
            "breakthrough": "Pointed rib vaults (directing load more vertically) + Flying Buttresses (external stone arches that transfer lateral roof thrust away from the walls onto external masonry piers)",
            "construction": "Ribbed vaulting, pinnacles on buttresses to add downward compressive ballast, and lead-camed stained glass windows",
            "monument": "Notre-Dame de Paris & Chartres Cathedral (France)",
            "outro": "Congratulations! You now understand the structural physics of Gothic flying buttresses! What ancient wonder should we analyze next? Leave a comment below!"
        }
    },
    {
        "id": "chinese-shinbashira-pagoda",
        "title": "How 1,400-Year-Old Wooden Pagodas Survived Deadly Earthquakes",
        "category": "Ancient Civil Engineering",
        "location": "Horyu-ji Pagoda, Nara, Japan & Fogong Temple, China",
        "map_region": "East Asia (Japan & China)",
        "source": "Ancient East Asian Timber Framing",
        "summary": "While modern concrete and masonry structures in Japan frequently crack or collapse under major earthquake shockwaves, 1,400-year-old five-story wooden pagodas have never been felled by an earthquake. The secret: they contain zero nails or rigid bolts. Each tier is connected by flexible interlocking timber brackets (Dougong), and running straight down the center is a massive suspended tree trunk called the Shinbashira. When ground shockwaves hit, the floors snake in alternating directions while the center trunk acts as an independent harmonic pendulum, dampening seismic sway!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "This 1,400-year-old wooden pagoda has survived 46 major earthquakes without a single nail. Here is how.",
            "The ancient earthquake shock-absorber hidden inside Asian pagodas: the floating Shinbashira tree trunk.",
            "Why rigid buildings break in earthquakes, and how ancient Japanese carpenters made towers snake like a snake."
        ],
        "engineering_steps": {
            "primitive": "Build a rigid tall multi-story timber tower fastened with iron nails",
            "flaw": "Ground shear forces shear iron fasteners; rigid frames snap under cyclic oscillation",
            "upgrade1": "Stack loose unfastened wooden floor pavilions",
            "flaw2": "Extreme wind storms blow individual roof eaves and floors out of alignment",
            "breakthrough": "Nail-free interlocking Dougong brackets + the Shinbashira (a massive central Cypress tree suspended from the roof rafters that acts as a tuned mass damper)",
            "construction": "Mortise and tenon joints, heavy overhanging eaves providing low center of gravity, and out-of-phase floor sway dissipation",
            "monument": "Horyu-ji Five-Story Pagoda (Nara, Japan)",
            "outro": "Congratulations! You just reverse-engineered the seismic damping of ancient timber pagodas! What structure should we decode next? Comment below!"
        }
    },
    {
        "id": "roman-pozzolana-harbor",
        "title": "Why Ancient Roman Concrete Grows Stronger When Struck by Seawater",
        "category": "Ancient Civil Engineering",
        "location": "Portus Cosanus & Baiae, Italy",
        "map_region": "Mediterranean Coast / Roman Italy",
        "source": "Roman Marine Materials Science",
        "summary": "Modern Portland cement breakwaters deteriorate within 50 years when exposed to saltwater, which corrodes steel rebar and leaches calcium hydroxide. Yet ancient Roman harbors made of concrete remain pristine after 2,000 years of pounding waves. Roman engineers mixed quicklime with volcanic ash (pozzolana) from the Gulf of Naples and seawater. When submerged, seawater triggers a rare geochemical reaction that grows interlocking aluminous tobermorite and phillipsite crystals inside the pores, reinforcing micro-cracks and making the concrete stronger over time!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "Modern concrete lasts 50 years in ocean water. Ancient Roman concrete lasts 2,000. Here is the lost recipe.",
            "The ancient volcanic concrete that actually gets stronger every time a wave hits it.",
            "How Roman engineers poured stone underwater that self-heals its own micro-cracks."
        ],
        "engineering_steps": {
            "primitive": "Build sea breakwaters from wooden pilings and loose boulders",
            "flaw": "Heavy ocean storm surges dislodge boulders and wood boring worms destroy timber",
            "upgrade1": "Pour standard lime mortar concrete into underwater forms",
            "flaw2": "Seawater dissolves standard lime before it can cure, washing the cement away",
            "breakthrough": "Mix slaked lime with volcanic ash (pozzolana) and volcanic tuff; seawater reacts with minerals to grow interlocking aluminous tobermorite crystals that heal micro-cracks",
            "construction": "Tightly joined wooden caisson forms lowered into ocean bays and packed with hot-mix volcanic mortar",
            "monument": "Portus Cosanus Marine Piers (Italy)",
            "outro": "Congratulations! You now understand the self-healing chemistry of ancient Roman marine concrete! Which ancient discovery should we break down next? Let me know in the comments!"
        }
    },
    {
        "id": "alexandria-pharos-lighthouse",
        "title": "How the 300-Foot Pharos Lighthouse Beamed Light 30 Miles at Sea",
        "category": "Ancient Civil Engineering",
        "location": "Pharos Island, Alexandria, Egypt",
        "map_region": "Hellenistic Egypt & Eastern Mediterranean",
        "source": "Hellenistic Optical & Structural Engineering",
        "summary": "Guiding trade ships into Alexandria's hazardous shallow harbor required a beacon visible from 30 miles away over the curvature of the Earth, requiring a tower over 300 feet tall on a storm-swept coastal reef. Sostratus of Cnidus designed a 3-tier aerodynamic structure: a massive square base to absorb wave impact, an octagonal middle section to deflect prevailing coastal gale winds, and a circular lantern top. Inside the lantern, a massive wood fire was magnified and focused by a precision-curved polished bronze concave mirror into a blazing beam across the sea!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did ancient engineers build a 350-foot skyscraper on a storm reef that beamed light 30 miles?",
            "The ancient mega-mirror that turned wood fires into an ocean lighthouse beam.",
            "How the Pharos of Alexandria stood for 1,500 years against Mediterranean hurricanes."
        ],
        "engineering_steps": {
            "primitive": "Bonfire on a coastal sand dune or natural headland",
            "flaw": "Low elevation limits visibility to 5 miles due to Earth's curvature; ships crash on outer reefs",
            "upgrade1": "Build a tall vertical stone chimney tower",
            "flaw2": "Gale-force ocean winds create vortex shedding that vibrates and topples tall square chimneys",
            "breakthrough": "Three aerodynamic tiers (Square base for wave absorption, Octagon midsection for wind deflection, Cylinder lantern) + giant curved parabolic polished bronze mirror",
            "construction": "Massive granite blocks joined with molten lead dowels, internal spiral ramp for pack animals hauling fuel wood to the top",
            "monument": "The Lighthouse of Alexandria (Seven Wonders of the Ancient World)",
            "outro": "Congratulations! You just reverse-engineered the optical and aerodynamic marvel of the Pharos Lighthouse! Which ancient wonder should we tackle next? Comment below!"
        }
    },
    {
        "id": "chand-baori-stepwell",
        "title": "How Ancient Indian Stepwells Kept Water Ice-Cold in 120°F Heat",
        "category": "Ancient Civil Engineering",
        "location": "Chand Baori, Abhaneri, Rajasthan, India",
        "map_region": "Thar Desert / Northwestern India",
        "source": "Ancient Indian Hydro-Architecture",
        "summary": "In the arid desert of Rajasthan, surface rainfall occurs only during brief monsoon months, while summer temperatures soar to 120°F, evaporating surface reservoirs. Master builders dug an inverted 13-story deep subterranean pyramid lined with 3,500 precision criss-crossing symmetrical stone steps. The steep geometric funnel creates a natural micro-climate: cool air sinks to the bottom while upper stepped walls shield the water from direct desert sunlight and hot winds, keeping the subterranean water reservoir 5 to 6 degrees Celsius cooler year-round!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How does an ancient 13-story upside-down stone pyramid keep water ice-cold in 120-degree desert heat?",
            "The mathematical stepwell with 3,500 steps that acts as a natural air conditioner.",
            "Why normal desert wells dry up, and how ancient Indian builders solved it with an inverted stone funnel."
        ],
        "engineering_steps": {
            "primitive": "Dig an open desert pond to catch monsoon rainwater",
            "flaw": "Extreme heat evaporates the entire pond in weeks; standing water breeds bacteria",
            "upgrade1": "Dig a narrow deep vertical well tube with a bucket rope",
            "flaw2": "Narrow tube cannot accommodate a town's water needs, and ropes break under heavy seasonal demand",
            "breakthrough": "Inverted stepped pyramid funnel: 3,500 precision stone steps across 13 subterranean stories creating a thermal trap where dense cold air pools at the water line",
            "construction": "Dry-stacked sandstone ashlar blocks with overflow drainage sluices, pavilions for shaded public retreat",
            "monument": "Chand Baori Stepwell (Rajasthan, India)",
            "outro": "Congratulations! You now understand the thermodynamic hydro-engineering behind Indian stepwells! Which ancient structure should we solve next? Drop your comment below!"
        }
    },
    {
        "id": "trajan-danube-bridge",
        "title": "How Trajan Built the World's Longest Bridge Across a Raging River",
        "category": "Ancient Civil Engineering",
        "location": "Iron Gates, Danube River, Romania/Serbia",
        "map_region": "Balkans & Roman Frontier",
        "source": "Roman Military Civil Engineering",
        "summary": "Invading Dacia required marching 100,000 Roman legionaries across the Danube River—a 3,700-foot wide torrent with freezing winter ice floes that smashed floating pontoon boat bridges. Architect Apollodorus of Damascus built 20 colossal masonry piers directly in the riverbed. To pour foundations underwater, soldiers drove concentric rings of double-walled oak timber piles into the riverbed, packed the gap with waterproof clay, and pumped out the water with Archimedes screws. They then erected 125-foot segmental wooden lattice arches, creating the longest bridge in the world for over 1,000 years!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did ancient Romans build a half-mile bridge across a roaring river in just two years?",
            "How Roman soldiers set stone foundations at the bottom of a 60-foot deep river without diving suits.",
            "The world's longest bridge for a millennium: Apollodorus of Damascus's engineering triumph."
        ],
        "engineering_steps": {
            "primitive": "Lash boats together into a floating pontoon bridge",
            "flaw": "Danube seasonal floods and winter floating ice floes smash and sever boat moorings",
            "upgrade1": "Drive single wooden pilings across the river to support a deck",
            "flaw2": "River current scours sediment from around pilings, collapsing the spans under military march resonance",
            "breakthrough": "Segmental wooden lattice truss arches spanning 125 feet between 20 monolithic stone piers set inside pumped-dry oak cofferdams",
            "construction": "Double-wall oak cofferdams sealed with clay, water pumped out via Archimedes screw pumps, pozzolanic core masonry piers",
            "monument": "Trajan's Bridge on the Danube (Romania/Serbia)",
            "outro": "Congratulations! You now understand how Roman engineers bridged the mighty Danube River! Which ancient engineering feat should we tackle next? Comment below!"
        }
    },
    {
        "id": "derinkuyu-underground-city",
        "title": "How an 18-Story Underground City for 20,000 People Was Carved",
        "category": "Ancient Civil Engineering",
        "location": "Derinkuyu, Cappadocia, Turkey",
        "map_region": "Central Anatolia / Cappadocia",
        "source": "Ancient Anatolian Subterranean Engineering",
        "summary": "When hostile armies swept through Cappadocia, surface villagers had no fortress walls to protect them. They discovered that the local volcanic tuff rock was soft and easily carved with bronze picks, but when exposed to air, the minerals oxidize and harden into rock. They tunneled down 18 stories (280 feet), carving homes, stables, wine presses, and churches. To prevent suffocation, they sank 180-foot vertical ventilation shafts that circulated fresh air to all levels, and protected entrances with 1,000-pound round stone disc doors that could only be rolled shut from the inside!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How did 20,000 ancient people live 18 stories underground without suffocating?",
            "The 280-foot underground city with 1,000-pound rolling stone vault doors.",
            "Why ancient engineers carved an entire civilization inside volcanic rock instead of building walls."
        ],
        "engineering_steps": {
            "primitive": "Hide in natural surface caves during an invasion",
            "flaw": "Invaders find cave openings and smoke out or trap occupants inside",
            "upgrade1": "Dig shallow underground cellars beneath homes",
            "flaw2": "Cellars lack ventilation; carbon dioxide pools and suffocates occupants within hours",
            "breakthrough": "18-story multi-tiered subterranean city with 55-meter master ventilation shafts circulating fresh air via convection, and 1,000-pound rolling millstone security doors",
            "construction": "Chiseling air-hardening volcanic tuff, gravity-separated waste wells, and covert escape tunnels linking to other subterranean towns",
            "monument": "Derinkuyu Underground City (Cappadocia, Turkey)",
            "outro": "Congratulations! You just explored the subterranean civil engineering of Derinkuyu! What ancient mystery should we uncover next? Tell me in the comments!"
        }
    },
    {
        "id": "great-wall-rice-mortar",
        "title": "How Sticky Rice Mortar Made the Great Wall of China Indestructible",
        "category": "Ancient Civil Engineering",
        "location": "Northern Frontier, China",
        "map_region": "East Asia / Northern China",
        "source": "Ancient Chinese Materials Science",
        "summary": "Building a 13,000-mile defensive stone wall across wind-scoured mountain ridges faced a deadly materials challenge: standard lime and earth mortars crumble within years under heavy rainfall and freezing winter freeze-thaw expansion cycles. Ming dynasty chemists invented a biological composite mortar: combining slaked lime with boiled sticky rice broth. The amylopectin polysaccharide in the rice forms a tight molecular web that prevents calcium carbonate crystals from breaking under stress, producing a waterproof, flexible mortar so dense that plant roots cannot penetrate it after 600 years!",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "Why the secret ingredient behind the Great Wall of China is the same thing in your kitchen: sticky rice.",
            "Modern mortar crumbles after decades. How ancient Chinese builders made mortar that lasts centuries using rice broth.",
            "The biological chemistry trick that made the Great Wall earthquake- and weather-proof."
        ],
        "engineering_steps": {
            "primitive": "Rammed earth walls (hangtu) tamped between wooden planks",
            "flaw": "Torrential monsoon rains erode and melt the earth ramparts over decades",
            "upgrade1": "Face the walls with kiln-fired bricks using standard slaked lime mortar",
            "flaw2": "Freezing winter temperatures cause water in mortar pores to expand, fracturing joints and allowing weeds to dislodge stones",
            "breakthrough": "Organic-inorganic composite: slaked lime mixed with amylopectin broth from boiled sticky rice, creating a dense, watertight seal that resists freeze-thaw cycles",
            "construction": "Quarried granite blocks, kiln-fired ceramic bricks, and high-temperature slaked lime boiling cauldrons along mountain ramparts",
            "monument": "The Great Wall of China (Ming Dynasty Sections)",
            "outro": "Congratulations! You now understand the biochemical materials engineering of the Great Wall of China! What should we build next? Let me know in the comments below!"
        }
    }
]

ENGLISH_ENGINEERING_CATALOG = [
    {
        "id": "panama-canal-gravity-locks",
        "title": "How the Panama Canal's Gravity-Fed Locks Lift Ships Over the Isthmus",
        "category": "Modern Water Infrastructure",
        "location": "Panama Canal, Panama",
        "map_region": "Atlantic and Pacific approaches, Gatun Lake, and the Central Cordillera",
        "source": "Panama Canal Authority",
        "references": [
            "https://pancanal.com/en/history-of-the-panama-canal/",
            "https://pancanal.com/en/design-of-the-locks/"
        ],
        "summary": "Show how lock chambers act as water lifts: gravity-fed culverts fill or empty a chamber to raise or lower ships between sea level and Gatun Lake. Map the route, show paired lock chambers and the lake-level crossing, then animate one vessel transit with a clear water-level cutaway. Verify measurements and any current operating claims against Panama Canal Authority sources.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How can a ship climb above sea level without a pump or a crane?",
            "The Panama Canal lifts ships with water—and gravity does the work.",
            "A ship crosses a mountain range inside a set of water-filled chambers."
        ],
        "engineering_steps": {
            "site": "Map the Atlantic and Pacific approaches, lock steps, and Gatun Lake",
            "mechanism": "Show gravity-fed culverts filling a chamber and lifting the ship",
            "sequence": "Animate gates closing, water leveling, gates opening, and repeated lock stages",
            "cutaway": "Expose the culverts and valves below the lock chamber",
            "payoff": "Show the ship reaching the lake and descending on the opposite side"
        }
    },
    {
        "id": "hoover-dam-diversion-tunnels",
        "title": "How Hoover Dam's River Diversion Tunnels Became Part of the Dam System",
        "category": "Modern Water Infrastructure",
        "location": "Black Canyon, Colorado River, United States",
        "map_region": "Colorado River and Black Canyon, Arizona–Nevada border",
        "source": "U.S. Bureau of Reclamation",
        "references": [
            "https://www.usbr.gov/lc/hooverdam/faqs/tunlfaqs.html",
            "https://www.usbr.gov/lc/hooverdam/faqs/damfaqs.html"
        ],
        "summary": "Explain how four canyon-wall tunnels carried the Colorado River around the dam construction site, how the main concrete structure combines gravity and arch action, and how diversion tunnels were later adapted into outlet/penstock works. Verify exact dimensions and sequence against Bureau of Reclamation sources.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "Before Hoover Dam could block the canyon, engineers had to give the Colorado River another route.",
            "The tunnels that moved the river during construction did not simply become useless afterward.",
            "How do you build a concrete dam where the river is already flowing?"
        ],
        "engineering_steps": {
            "site": "Map Black Canyon and the river's original route",
            "temporary_works": "Cut to the four diversion tunnels through opposite canyon walls",
            "construction": "Show cofferdams isolating the work area and concrete lifts forming the curved dam",
            "mechanism": "Illustrate gravity and horizontal arch action together",
            "reuse": "Show verified tunnel conversion into outlet/penstock routes"
        }
    },
    {
        "id": "thames-barrier-sector-gates",
        "title": "How the Thames Barrier's Gates Rise to Hold Back a Storm Surge",
        "category": "Modern Flood Engineering",
        "location": "River Thames at Woolwich, London, England",
        "map_region": "Tidal Thames and London, United Kingdom",
        "source": "UK Environment Agency / GOV.UK",
        "references": [
            "https://www.gov.uk/guidance/the-thames-barrier",
            "https://www.gov.uk/guidance/managing-future-flood-risk-and-thames-barrier-thames-estuary-2100"
        ],
        "summary": "A cross-section explainer of the Thames Barrier's movable gates: how lowered gates allow river traffic, how gates are raised ahead of a storm tide, and why they remain closed until downstream and upstream levels are managed. Distinguish the barrier from the wider estuary flood-defence network and verify current operating facts from the Environment Agency.",
        "curiosity_score": 10,
        "assigned_style": "tall-tale",
        "hook_angles": [
            "How can a barrier across a working river disappear below the water when ships need to pass?",
            "London's flood gate waits underwater—until a storm surge turns the river into a wall.",
            "Why does the Thames Barrier stay shut even after the storm surge peaks?"
        ],
        "engineering_steps": {
            "site": "Map the tidal Thames and the Woolwich crossing",
            "normal_state": "Show a lowered sector gate resting on the riverbed and a vessel passing",
            "operation": "Animate the gate rotating upward to block incoming tidal surge",
            "water_levels": "Compare downstream and upstream levels during closure and reopening",
            "payoff": "Show how gates work within the wider flood-defence system, without implying the barrier alone protects all of London"
        }
    }
]

# Concepts lead the English scout; mega-projects remain an occasional lane.
ENGLISH_TOPIC_CATALOG = ENGLISH_CONCEPT_CATALOG + ENGLISH_MODERN_ENGINEERING_CATALOG + ENGLISH_ENGINEERING_CATALOG


def load_done_topics():
    if not LEDGER.exists():
        return set()
    text = LEDGER.read_text(errors="replace").lower()
    done = set()
    for line in text.splitlines():
        if line.startswith("- "):
            parts = line[2:].split("|")
            if len(parts) >= 2:
                topic = parts[1].strip()
                done.add(topic)
                for w in re.findall(r"\b[a-z]{4,}\b", topic):
                    done.add(w)
                # Also index Telugu words
                for tw in re.findall(r"[\u0c00-\u0c7f]{3,}", topic):
                    done.add(tw)
    return done



def hunt_english_topics(top_n=6, target_style=None):
    """Return fresh concept-led topics plus occasional engineering projects."""
    done_keywords = load_done_topics()
    results = []

    for item in ENGLISH_TOPIC_CATALOG:
        if target_style == "cinematic-what-if":
            lane = item.get("topic_lane", "")
            if lane not in {"psychology", "perception", "body-brain", "behavior"}:
                continue
        is_done = False
        item_title_lower = item["title"].lower()
        # Treat a project name as done when its two identifying words have
        # already appeared in a ledger entry (e.g. "Hoover Dam" or "Panama Canal").
        identity = item["id"].split("-")[:2]
        if len(identity) == 2 and all(term in done_keywords for term in identity):
            is_done = True
        candidate_title = item.get("what_if_title", "").lower() if target_style == "cinematic-what-if" else ""
        if item_title_lower in done_keywords or item["id"] in done_keywords or (candidate_title and candidate_title in done_keywords):
            is_done = True
        else:
            # Check key keywords
            for kw in [item["id"], item.get("location", "").lower(), item["title"].lower()]:
                if kw and kw in done_keywords:
                    is_done = True
                    break

        if is_done:
            continue

        results.append({
            "id": item["id"],
            "source": item["source"],
            "title": item.get("what_if_title", item["title"]) if target_style == "cinematic-what-if" else item["title"],
            **({"source_title": item["title"]} if target_style == "cinematic-what-if" else {}),
            "category": item["category"],
            "topic_lane": item.get("topic_lane", "engineering"),
            "location": item["location"],
            "map_region": item["map_region"],
            "description": item["summary"],
            "summary": item["summary"],
            "link": "#",
            "score": item["curiosity_score"] * 10,
            "curiosity_score": item["curiosity_score"],
            "assigned_style": target_style or item.get("assigned_style", "tall-tale"),
            "suggested_hooks": item["hook_angles"],
            "hook_angles": item["hook_angles"],
            "engineering_steps": item.get("engineering_steps", {}),
            "references": item.get("references", []),
            "channel": "curiography",
        })

    return results[:top_n]


def hunt_telugu_topics(top_n=6, category_key=None, target_style=None):
    """Returns curated Telugu topics filtered against the ledger topics-done.md."""
    done_keywords = load_done_topics()
    results = []

    for item in TELUGU_TOPICS_CATALOG:
        if category_key and item.get("category_key") != category_key:
            continue
        if target_style and target_style != "tall-tale" and item.get("assigned_style") != target_style:
            continue

        # Check if already done
        is_done = False
        item_title_lower = item["title"].lower()
        if item_title_lower in done_keywords:
            is_done = True
        else:
            for tw in re.findall(r"[\u0c00-\u0c7f]{4,}", item["title"]):
                if tw in done_keywords and tw not in {"రహస్యం", "కథ", "ఏమిటి", "ఎందుకు", "దేవాలయం"}:
                    is_done = True
                    break

        if is_done:
            continue

        results.append({
            "source": item["source"],
            "title": item["title"],
            "english_title": item.get("english_title", ""),
            "category": item["category"],
            "category_key": item.get("category_key", "general"),
            "deity": item.get("deity", ""),
            "description": item["summary"],
            "summary": item["summary"],
            "link": "#",
            "score": item["curiosity_score"] * 10,
            "curiosity_score": item["curiosity_score"],
            "assigned_style": item["assigned_style"],
            "suggested_hooks": item["hook_angles"],
            "hook_angles": item["hook_angles"],
            "channel": "asakthi",
        })

    return results[:top_n]


def fetch_feed(feed_info):
    items = []
    try:
        req = urllib.request.Request(
            feed_info["url"],
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)

            for item in root.findall(".//item"):
                title_elem = item.find("title")
                desc_elem = item.find("description")
                link_elem = item.find("link")

                title = html.unescape(title_elem.text if title_elem is not None and title_elem.text else "").strip()
                desc = html.unescape(desc_elem.text if desc_elem is not None and desc_elem.text else "").strip()
                desc_clean = re.sub(r"<[^>]+>", " ", desc).strip()
                link = link_elem.text if link_elem is not None and link_elem.text else ""

                if title:
                    items.append({
                        "source": feed_info["source"],
                        "title": title,
                        "description": desc_clean[:280],
                        "link": link
                    })
    except Exception:
        pass
    return items


def score_item(item, target_style, done_keywords):
    title_lower = item["title"].lower()
    desc_lower = item["description"].lower()
    combined = title_lower + " " + desc_lower

    # 1. Negative filter check
    for bad in EXCLUDE_WORDS:
        if re.search(r"\b" + re.escape(bad) + r"\b", combined):
            return -100

    # 2. Check if already covered in ledger
    for word in re.findall(r"\b[a-z]{5,}\b", title_lower):
        if word in done_keywords and word not in {"what", "happens", "brain", "human", "water", "world", "their"}:
            return -50

    score = 10

    # 3. Curiosity / Hook Triggers
    curiosity_patterns = [
        r"\bwhy\b", r"\bhow\b", r"\bwhat happens\b", r"\bsecret\b", r"\bhidden\b",
        r"\bdiscovered\b", r"\bresearchers find\b", r"\bunexpected\b", r"\bmystery\b",
        r"\bancient\b", r"\bbizarre\b", r"\bsurvive\b", r"\bdangerous\b", r"\brisk\b",
        r"\bfirst time\b", r"\brecord\b", r"\bshocking\b"
    ]
    for pat in curiosity_patterns:
        if re.search(pat, combined):
            score += 15

    # 4. Genre Alignment
    if target_style and target_style in GENRE_KEYWORDS:
        genre_matches = sum(1 for kw in GENRE_KEYWORDS[target_style] if kw in combined)
        score += genre_matches * 12
    else:
        for s_name, kws in GENRE_KEYWORDS.items():
            matches = sum(1 for kw in kws if kw in combined)
            if matches > 0:
                score += matches * 6

    if re.search(r"\b\d+\b", item["title"]):
        score += 8

    return score


def generate_hook_angles(title):
    clean = re.sub(r"^[A-Z0-9\s]+:\s*", "", title).strip().rstrip("?.!")
    return [
        f"The surprising mechanism behind: {clean}.",
        f"What is your brain or body doing when {clean.lower()}?",
        f"Why does this familiar effect happen: {clean}?"
    ]


def hunt_live_english_topics(top_n=2, target_style=None):
    """Rank a small set of live feed stories that fit the concept-explainer lanes."""
    done = load_done_topics()
    signals = ("psychology", "instinct", "behavior", "behaviour", "brain", "mind", "memory",
               "attention", "perception", "decision", "emotion", "body", "human", "animal",
               "sleep", "dream", "voice", "yawn", "touch", "tickle", "smell", "taste",
               "sense", "habit", "eye", "hearing", "physics", "material", "dam", "bridge",
               "tunnel", "canal", "river", "flood", "architecture", "engineering", "structure")
    rows, seen = [], set()
    for feed in FEEDS:
        for item in fetch_feed(feed):
            title = item["title"].strip()
            key = title.lower()
            if len(title) < 18 or key in seen:
                continue
            seen.add(key)
            combined = (title + " " + item.get("description", "")).lower()
            if not any(term in combined for term in signals):
                continue
            score = score_item(item, None, done)
            if score < 22:
                continue
            topic_lane = "engineering" if any(k in combined for k in ("dam", "bridge", "tunnel", "canal", "river", "flood", "engineering", "structure")) else "concept"
            if target_style == "cinematic-what-if":
                what_if_signals = ("psychology", "instinct", "behavior", "behaviour", "brain", "mind", "memory",
                                   "attention", "perception", "decision", "emotion", "body", "human", "animal",
                                   "sleep", "dream", "voice", "yawn", "touch", "tickle", "smell", "taste",
                                   "sense", "habit", "eye", "hearing", "reflex", "reaction", "pain", "vision")
                if topic_lane == "engineering" or not any(term in combined for term in what_if_signals):
                    continue
            rows.append({
                "source": item["source"], "title": title, "description": item.get("description", ""),
                "summary": item.get("description", ""), "link": item.get("link", ""),
                "category": "Live science and concept story", "topic_lane": topic_lane,
                "score": score, "curiosity_score": min(10, max(6, int(score / 6))),
                "assigned_style": target_style or "tall-tale", "suggested_hooks": generate_hook_angles(title),
                "hook_angles": generate_hook_angles(title), "references": [item.get("link", "")],
                "channel": "curiography"
            })
    rows.sort(key=lambda row: row["score"], reverse=True)
    return rows[:top_n]


def hunt_trends(target_style=None, top_n=5, channel="en", category_key=None):
    if channel == "te":
        return hunt_telugu_topics(top_n=top_n, category_key=category_key, target_style=target_style)

    # English defaults to compact concept explainers; live concepts appear first,
    # while vetted evergreen candidates ensure discovery still works offline.
    live = hunt_live_english_topics(top_n=min(2, max(0, top_n // 4)), target_style=target_style)
    curated = hunt_english_topics(top_n=top_n, target_style=target_style)
    if live or curated:
        live_titles = {row["title"].lower() for row in live}
        evergreen = [row for row in curated if row["title"].lower() not in live_titles]
        return (live + evergreen)[:top_n]

    done_keywords = load_done_topics()
    all_items = []

    for f in FEEDS:
        all_items.extend(fetch_feed(f))

    ranked = []
    seen_titles = set()

    for it in all_items:
        clean_title = it["title"].strip()
        if clean_title in seen_titles or len(clean_title) < 15:
            continue
        seen_titles.add(clean_title)

        s = score_item(it, target_style, done_keywords)
        if s > 0:
            curiosity = min(10, max(6, int(s / 6)))
            assigned = target_style
            if not assigned:
                best_g, best_c = "engineering-explainer", 0
                comb = (it["title"] + " " + it["description"]).lower()
                for g_name, kws in GENRE_KEYWORDS.items():
                    c = sum(1 for kw in kws if kw in comb)
                    if c > best_c:
                        best_g, best_c = g_name, c
                assigned = best_g

            hooks = generate_hook_angles(it["title"])
            ranked.append({
                "source": it["source"],
                "title": it["title"],
                "description": it["description"],
                "summary": it["description"],
                "link": it["link"],
                "score": s,
                "curiosity_score": curiosity,
                "assigned_style": assigned,
                "suggested_hooks": hooks,
                "hook_angles": hooks,
                "channel": "curiography",
            })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Hunt viral trending topics for faceless shorts")
    parser.add_argument("--channel", choices=["en", "te", "all"], default="en", help="Target channel (en=curiography, te=asakthi)")
    parser.add_argument("--category", help="Category filter for Telugu (temples, epics, science_tradition, legends)")
    parser.add_argument("--style", choices=["engineering-explainer", "tall-tale", "cinematic-what-if"], help="Target visual style")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    parser.add_argument("--count", type=int, default=5, help="Number of trends to output")
    args = parser.parse_args()

    if args.channel == "te" and args.style == "cinematic-what-if":
        parser.error("cinematic-what-if is English-only; Asakthi keeps its selected Telugu style")

    trends = hunt_trends(target_style=args.style, top_n=args.count, channel=args.channel, category_key=args.category)

    if args.json:
        print(json.dumps(trends, indent=2, ensure_ascii=False))
        return

    ch_label = "🇮🇳 TELUGU (Asakthi)" if args.channel == "te" else "🇬🇧 ENGLISH (Curiography)"
    print(f"\n🔥 TOP TRENDING SHORTS TOPICS [{ch_label}]\n" + "=" * 65)
    for i, t in enumerate(trends, 1):
        print(f"\n#{i} [Curiosity: {t['curiosity_score']}/10] {t['title']}")
        if t.get("english_title"):
            print(f"   Sub: {t['english_title']}")
        print(f"   Source: {t['source']} | Style: {t['assigned_style']}")
        print(f"   Summary: {t['summary'][:140]}...")
        print(f"   Viral Hooks:")
        for h in t["suggested_hooks"]:
            print(f"     • {h}")
    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    main()
