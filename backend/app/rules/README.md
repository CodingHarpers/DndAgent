## Preparation
Use preprocessed kb files, or
1. deploy [dnd api](https://www.dnd5eapi.co/) and run `download_data.py`.
2. run `process_kb.py` to parse raw api content to rule knowledge base.
## ingested file statics
```
Successfully loaded 1152 logic documents.
Document Length Statistics (characters):
  Count: 1152
  Min: 280
  Max: 9812
  Average: 1169.97
  Median: 718.5
```
## ingested file example in the vector store (optimzed and chunked for searching)
```
Name: Fighter
Description: The Fighter class focuses on mastery of combat, granting powerful martial abilities and a high number of attacks. Fighters gain a d10 Hit Die, proficiency in all armor, shields, simple and martial weapons, and Strength and Constitution saving throws. They choose two skills from a specific list. Their progression involves gaining Fighting Styles, Action Surges for extra actions, the ability to reroll failed saves with Indomitable, and multiple opportunities for Extra Attack, allowing them to make up to three attacks per action. They also select a Martial Archetype at level 3, which grants additional features at levels 3, 7, 10, 15, and 18, specializing their combat style. Fighters receive numerous Ability Score Improvements throughout their career.
--- Rules ---
Logic: IF Class Selected is Fighter (Character Creation) THEN Hit Die is d10 AND Grant Proficiency: All Armor, Shields, Simple Weapons, Martial Weapons, Saving Throw: STR, Saving Throw: CON AND Choose two skills from Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, and Survival
Keywords: starting stats, fighter hp, fighter proficiencies, armor proficiency, weapon proficiency, saving throws
Logic: IF Class Level == 1 (Reach Level 1) THEN Set Proficiency Bonus to 2
Keywords: proficiency modifier, prof bonus, level 1 stats
Logic: IF Class Level == 1 (Reach Level 1) THEN Gain Feature: Fighting Style AND Gain Feature: Second Wind
Keywords: level 1 fighter, starting features, fighting style choice
Logic: IF Class Level == 2 (Reach Level 2) THEN Set Max Action Surges to 1
Keywords: action surge uses, fighter action
Logic: IF Class Level == 2 (Reach Level 2) THEN Gain Feature: Action Surge (1 use)
Keywords: level 2 fighter, action surge uses, extra action
Logic: IF Class Level == 3 (Reach Level 3) THEN Gain Feature: Martial Archetype
Keywords: level 3 fighter, subclass, fighter archetype
Logic: IF Class Level == 4 (Reach Level 4) THEN Gain Feature: Ability Score Improvement
Keywords: level 4 fighter, asi, ability scores
Logic: IF Class Level == 5 (Reach Level 5) THEN Set Proficiency Bonus to 3 AND Set Number of Extra Attacks to 1
Keywords: proficiency modifier, prof bonus, extra attack count
Logic: IF Class Level == 5 (Reach Level 5) THEN Gain Feature: Extra Attack
Keywords: level 5 fighter, multiple attacks
Logic: IF Class Level == 6 (Reach Level 6) THEN Gain Feature: Ability Score Improvement
Keywords: level 6 fighter, asi, ability scores
Logic: IF Class Level == 7 (Reach Level 7) THEN Gain Feature: Martial Archetype feature
Keywords: level 7 fighter, subclass feature
Logic: IF Class Level == 8 (Reach Level 8) THEN Gain Feature: Ability Score Improvement
Keywords: level 8 fighter, asi, ability scores
Logic: IF Class Level == 9 (Reach Level 9) THEN Set Proficiency Bonus to 4 AND Set Max Indomitable Uses to 1
Keywords: proficiency modifier, prof bonus, indomitable uses
Logic: IF Class Level == 9 (Reach Level 9) THEN Gain Feature: Indomitable (1 use)
Keywords: level 9 fighter, reroll save
Logic: IF Class Level == 10 (Reach Level 10) THEN Gain Feature: Martial Archetype feature
Keywords: level 10 fighter, subclass feature
Logic: IF Class Level == 11 (Reach Level 11) THEN Set Number of Extra Attacks to 2
Keywords: extra attack count, more attacks
Logic: IF Class Level == 11 (Reach Level 11) THEN Gain Feature: Extra Attack (2)
Keywords: level 11 fighter, multiple attacks
Logic: IF Class Level == 12 (Reach Level 12) THEN Gain Feature: Ability Score Improvement
Keywords: level 12 fighter, asi, ability scores
Logic: IF Class Level == 13 (Reach Level 13) THEN Set Proficiency Bonus to 5 AND Set Max Indomitable Uses to 2
Keywords: proficiency modifier, prof bonus, indomitable uses
Logic: IF Class Level == 13 (Reach Level 13) THEN Gain Feature: Indomitable (2 uses)
Keywords: level 13 fighter, reroll save
Logic: IF Class Level == 14 (Reach Level 14) THEN Gain Feature: Ability Score Improvement
Keywords: level 14 fighter, asi, ability scores
Logic: IF Class Level == 15 (Reach Level 15) THEN Gain Feature: Martial Archetype feature
Keywords: level 15 fighter, subclass feature
Logic: IF Class Level == 16 (Reach Level 16) THEN Gain Feature: Ability Score Improvement
Keywords: level 16 fighter, asi, ability scores
Logic: IF Class Level == 17 (Reach Level 17) THEN Set Proficiency Bonus to 6 AND Set Max Action Surges to 2 AND Set Max Indomitable Uses to 3
Keywords: proficiency modifier, prof bonus, action surge uses, indomitable uses
Logic: IF Class Level == 17 (Reach Level 17) THEN Gain Feature: Action Surge (2 uses) AND Gain Feature: Indomitable (3 uses)
Keywords: level 17 fighter, extra action, reroll save
Logic: IF Class Level == 18 (Reach Level 18) THEN Gain Feature: Martial Archetype feature
Keywords: level 18 fighter, subclass feature
Logic: IF Class Level == 19 (Reach Level 19) THEN Gain Feature: Ability Score Improvement
Keywords: level 19 fighter, asi, ability scores
Logic: IF Class Level == 20 (Reach Level 20) THEN Set Number of Extra Attacks to 3
Keywords: extra attack count, more attacks
Logic: IF Class Level == 20 (Reach Level 20) THEN Gain Feature: Extra Attack (3)
Keywords: level 20 fighter, capstone
Tags: fighter class, fighter dnd, fighter levels, combatant, martial class
```
## Rule-Based Context Example


```
--- Context ---
--- Document: Fighter ---
The Fighter class focuses on mastery of combat, granting powerful martial abilities and a high number of attacks. Fighters gain a d10 Hit Die, proficiency in all armor, shields, simple and martial weapons, and Strength and Constitution saving throws. They choose two skills from a specific list. Their progression involves gaining Fighting Styles, Action Surges for extra actions, the ability to reroll failed saves with Indomitable, and multiple opportunities for Extra Attack, allowing them to make up to three attacks per action. They also select a Martial Archetype at level 3, which grants additional features at levels 3, 7, 10, 15, and 18, specializing their combat style. Fighters receive numerous Ability Score Improvements throughout their career.

--- Document: Martial Archetype ---
At 3rd level, you choose an archetype that you strive to emulate in your combat styles and techniques, such as Champion. The archetype you choose grants you features at 3rd level and again at 7th, 10th, 15th, and 18th level.

--- Document: Martial Archetype Feature ---
At 3rd level, you choose an archetype that you strive to emulate in your combat styles and techniques, such as Champion. The archetype you choose grants you features at 3rd level and again at 7th, 10th, 15th, and 18th level.

--- Document: Fighter ---
The Fighter class focuses on mastery of combat, granting powerful martial abilities and a high number of attacks. Fighters gain a d10 Hit Die, proficiency in all armor, shields, simple and martial weapons, and Strength and Constitution saving throws. They choose two skills from a specific list. Their progression involves gaining Fighting Styles, Action Surges for extra actions, the ability to reroll failed saves with Indomitable, and multiple opportunities for Extra Attack, allowing them to make up to three attacks per action. They also select a Martial Archetype at level 3, which grants additional features at levels 3, 7, 10, 15, and 18, specializing their combat style. Fighters receive numerous Ability Score Improvements throughout their career.

--- Document: Martial Archetype ---
At 3rd level, you choose an archetype that you strive to emulate in your combat styles and techniques, such as Champion. The archetype you choose grants you features at 3rd level and again at 7th, 10th, 15th, and 18th level.

--- Document: Additional Fighting Style ---
At 10th level, you can choose a second option from the Fighting Style class feature.
--- RULES ---
[Fighter] IF Class Level == 1 (Trigger: Reach Level 1) THEN Set Proficiency Bonus to 2
[Fighter] IF Class Level == 1 (Trigger: Reach Level 1) THEN Gain Feature: Fighting Style AND Gain Feature: Second Wind
[Fighter] IF Class Level == 2 (Trigger: Reach Level 2) THEN Set Max Action Surges to 1
[Fighter] IF Class Level == 2 (Trigger: Reach Level 2) THEN Gain Feature: Action Surge (1 use)
[Fighter] IF Class Level == 3 (Trigger: Reach Level 3) THEN Gain Feature: Martial Archetype
[Fighter] IF Class Level == 4 (Trigger: Reach Level 4) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 5 (Trigger: Reach Level 5) THEN Set Proficiency Bonus to 3 AND Set Number of Extra Attacks to 1
[Fighter] IF Class Level == 5 (Trigger: Reach Level 5) THEN Gain Feature: Extra Attack
[Fighter] IF Class Level == 6 (Trigger: Reach Level 6) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 7 (Trigger: Reach Level 7) THEN Gain Feature: Martial Archetype feature
[Fighter] IF Class Level == 8 (Trigger: Reach Level 8) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 9 (Trigger: Reach Level 9) THEN Set Proficiency Bonus to 4 AND Set Max Indomitable Uses to 1
[Fighter] IF Class Level == 9 (Trigger: Reach Level 9) THEN Gain Feature: Indomitable (1 use)
[Fighter] IF Class Level == 10 (Trigger: Reach Level 10) THEN Gain Feature: Martial Archetype feature
[Fighter] IF Class Level == 11 (Trigger: Reach Level 11) THEN Set Number of Extra Attacks to 2
[Fighter] IF Class Level == 11 (Trigger: Reach Level 11) THEN Gain Feature: Extra Attack (2)
[Fighter] IF Class Level == 12 (Trigger: Reach Level 12) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 13 (Trigger: Reach Level 13) THEN Set Proficiency Bonus to 5 AND Set Max Indomitable Uses to 2
[Fighter] IF Class Level == 13 (Trigger: Reach Level 13) THEN Gain Feature: Indomitable (2 uses)
[Fighter] IF Class Level == 14 (Trigger: Reach Level 14) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 15 (Trigger: Reach Level 15) THEN Gain Feature: Martial Archetype feature
[Fighter] IF Class Level == 16 (Trigger: Reach Level 16) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 17 (Trigger: Reach Level 17) THEN Set Proficiency Bonus to 6 AND Set Max Action Surges to 2 AND Set Max Indomitable Uses to 3
[Fighter] IF Class Level == 17 (Trigger: Reach Level 17) THEN Gain Feature: Action Surge (2 uses) AND Gain Feature: Indomitable (3 uses)
[Fighter] IF Class Level == 18 (Trigger: Reach Level 18) THEN Gain Feature: Martial Archetype feature
[Fighter] IF Class Level == 19 (Trigger: Reach Level 19) THEN Gain Feature: Ability Score Improvement
[Fighter] IF Class Level == 20 (Trigger: Reach Level 20) THEN Set Number of Extra Attacks to 3
[Fighter] IF Class Level == 20 (Trigger: Reach Level 20) THEN Gain Feature: Extra Attack (3)
[Martial Archetype Feature] IF Character is a Fighter (Trigger: Character gains 3rd Fighter level) THEN Character chooses a Martial Archetype (e.g., Champion)
[Martial Archetype Feature] IF Character is a Fighter AND has chosen a Martial Archetype AND reaches 3rd, 7th, 10th, 15th, or 18th level (Trigger: Character gains Fighter levels) THEN Character gains features from their chosen Martial Archetype
[Martial Archetype] IF N/A (Trigger: Player reaches Fighter Level 3) THEN Player chooses one Martial Archetype option
[Martial Archetype] IF Player has chosen a Martial Archetype (Trigger: Player reaches Fighter Level 3, 7, 10, 15, or 18) THEN Player gains features from their chosen Martial Archetype
[Martial Archetype Feature] IF Character is a Fighter (Trigger: Character gains 3rd Fighter level) THEN Character chooses a Martial Archetype (e.g., Champion)
[Martial Archetype Feature] IF Character is a Fighter AND has chosen a Martial Archetype AND reaches 3rd, 7th, 10th, 15th, or 18th level (Trigger: Character gains Fighter levels) THEN Character gains features from their chosen Martial Archetype
[Martial Archetype] IF Character is a Fighter (Trigger: Character reaches 3rd level) THEN Character chooses a Martial Archetype
[Martial Archetype] IF Character is 3rd level AND Character is a Fighter (Trigger: Character chooses a Martial Archetype) THEN Character gains Martial Archetype features specific to 3rd level
[Martial Archetype] IF Character has chosen a Martial Archetype AND Character is a Fighter (Trigger: Character reaches 7th level) THEN Character gains Martial Archetype features specific to 7th level
[Martial Archetype] IF Character has chosen a Martial Archetype AND Character is a Fighter (Trigger: Character reaches 10th level) THEN Character gains Martial Archetype features specific to 10th level
[Martial Archetype] IF Character has chosen a Martial Archetype AND Character is a Fighter (Trigger: Character reaches 15th level) THEN Character gains Martial Archetype features specific to 15th level
[Martial Archetype] IF Character has chosen a Martial Archetype AND Character is a Fighter (Trigger: Character reaches 18th level) THEN Character gains Martial Archetype features specific to 18th level
[Martial Archetype Feature] IF None (Trigger: Player gains Fighter level 3) THEN Player chooses one Martial Archetype
[Martial Archetype Feature] IF Player has chosen a Martial Archetype (Trigger: Player gains Fighter levels) THEN Chosen Martial Archetype grants features at 3rd, 7th, 10th, 15th, and 18th level
[Fighter] IF Class Selected is Fighter (Trigger: Character Creation) THEN Hit Die is d10 AND Grant Proficiency: All Armor, Shields, Simple Weapons, Martial Weapons, Saving Throw: STR, Saving Throw: CON AND Choose two skills from Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, and Survival
```

## Lawyer Response Example
```
Q: The player is casting a spell and the target is immune to the spell.
A: **Rule Interpretation:**
When a creature is immune to a spell, the spell's effects fail to manifest on that specific target. The spell is still considered cast, and any spell slot or components are expended, but the immune target experiences no direct impact from the spell. This immunity can arise from various conditions, such as being a specific creature type for certain spells (e.g., constructs or undead for *Heal*), possessing immunity to a core condition of the spell (e.g., immunity to the charmed condition for *Irresistible Dance* or *Suggestion*), being a shapechanger for *True Polymorph*, or being protected by another effect like *Mind Blank* against divination spells or certain *Wish* effects.

**DM Action Items:**
*   Inform the player that the target is immune to the spell.
*   Confirm that the spell slot and any consumed material components are expended, as the spell was successfully cast but failed to affect the immune target.
*   State that the spell's intended effect on that target does not occur.

**Logic Trace:**
*   IF "The player is casting a spell"
*   AND "the target is immune to the spell" (Trigger: On Cast/Initial spell effect, based on specific spell rules such as `[Irresistible Dance] IF Target is immune to the Charmed condition THEN Target is immune to this spell`, `[Suggestion] IF Target is immune to the charmed condition THEN Target is immune to this spell`, `[True Polymorph] IF Target creature is a Shapechanger THEN Spell has no effect on target`, `[Heal] IF Target is a Construct THEN Spell has no effect on target`, or protection from another spell like `[Mind Blank] IF Target is under the effect of Mind Blank (Trigger: A divination spell attempts to affect target) THEN The divination spell fails to affect target`)
*   THEN "Target is immune to this spell" OR "Spell has no effect on target."
*   THEREFORE, the spell's effects do not apply to the specified immune target.
```
