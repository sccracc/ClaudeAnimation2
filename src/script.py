# The only topic-specific input lives in TOPIC; the script lines below were written for it.
TOPIC = "How does your brain create dreams while you sleep?"
LINES = [
    "Tonight, while you sleep, your brain will make a movie... starring you.",
    "Every ninety minutes or so, you drift into REM sleep, when the most vivid dreams happen.",
    "A switch in your brainstem flips on.",
    "Your hippocampus, the memory keeper, digs out scraps from today... and from long ago.",
    "Your emotion center glows, while your logic center, the prefrontal cortex, dozes off.",
    "So nobody asks why your school is floating at sea.",
    "Meanwhile, your muscles go limp, so you don't act it out.",
    "Scientists still debate why we dream. It may help sort memories and soothe feelings.",
    "Then morning comes... and most of the movie is gone by breakfast.",
]
VOICE = dict(model='openai/gpt-audio', voice='ash')
INSTRUCTIONS = ("You are the narrator of a gentle, whimsical animated short film. Read the user's text aloud exactly as written, "
 "word for word, adding and changing nothing. Voice: a calm, warm, relaxed man, slightly low but natural. Conversational, like "
 "quietly explaining something fascinating to a friend late at night, with a hint of a smile. Natural relaxed pace (not slow, "
 "not sleepy), clear diction, subtle feeling. Leave a short natural pause between sentences and a gentle pause at each ellipsis. "
 "Not an announcer, not theatrical.")
