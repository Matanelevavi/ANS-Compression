#pragma once
#include <cstddef>

// Public, well-known text used to prime the adaptive model
// (paper, Section 3.2). The text itself is not secret: the point is
// that the model updates while reading it are gated by the secret
// key, so the model state AFTER priming is secret. This closes the
// weakness of a publicly known initial model.
//
// The text is the opening of "Moby-Dick" by Herman Melville (1851),
// which is in the public domain.
static const char PRIMING_TEXT[] =
    "Call me Ishmael. Some years ago - never mind how long precisely - "
    "having little or no money in my purse, and nothing particular to "
    "interest me on shore, I thought I would sail about a little and see "
    "the watery part of the world. It is a way I have of driving off the "
    "spleen and regulating the circulation. Whenever I find myself "
    "growing grim about the mouth; whenever it is a damp, drizzly "
    "November in my soul; whenever I find myself involuntarily pausing "
    "before coffin warehouses, and bringing up the rear of every funeral "
    "I meet; and especially whenever my hypos get such an upper hand of "
    "me, that it requires a strong moral principle to prevent me from "
    "deliberately stepping into the street, and methodically knocking "
    "people's hats off - then, I account it high time to get to sea as "
    "soon as I can. This is my substitute for pistol and ball. With a "
    "philosophical flourish Cato throws himself upon his sword; I "
    "quietly take to the ship. There is nothing surprising in this.";

static const size_t PRIMING_TEXT_LENGTH = sizeof(PRIMING_TEXT) - 1;
