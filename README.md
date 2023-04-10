# 💡 Bulb Control

Code I wrote for managing the Wyze Color Bulbs in my home. My main goal is saving and loading the state of multiple lights (scenes).

Scenes are saved as JSON files containing the states of all lights. The ones for my home live in the `scenes/` directory.

The lights can be saved and loaded through the `bulbs.py` CLI tool. There's also a Flask server and minimal web page to provide a rudimentary UI.

This is tailored pretty hard to my situation, but it should be tweakable to work in a general setting without too much work.

## Usage

### Getting Started

Add your Wyze credentials to a file called `credentials.json` in the root directory that looks like this:

```
{
  "email": "[email]",
  "password": "[password]"
}
```

### Save

```
$ python bulbs.py save [scene_name]
```

Save the state of all lights to `scenes/[scene_name].json`.

### Load

```
$ python bulbs.py load [scene_name]
```

Will set all the lights to the state listed in the scene file.
