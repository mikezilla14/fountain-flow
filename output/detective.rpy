label start:
    $ PLAYER_HP = 100
    $ HAS_KEY = false

    # INT. ANCIENT RUINS - NIGHT

    scene ruins_dark_stormy

    play music "tension_loop_v2"

    "The wind howls through the cracked masonry."

    show Elara, nervous, left

    Elara "We shouldn't be here."

    menu:
        "What do you do?"

        "Force Door":
            "Kick the door open."
            jump 

        if PLAYER_HP > 10:

            $ PLAYER_HP -= 5

            "The wood splinters. You are in."

            jump SCENE_INTERIOR

        else:

            "You are too weak."

            jump SCENE_FAIL

            "Use Key":
                "Unlock it carefully."
                jump 

            if HAS_KEY == true:

                "The mechanism clicks. Smooth."

                jump SCENE_INTERIOR
