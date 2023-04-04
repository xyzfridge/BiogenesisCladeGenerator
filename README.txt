~~~Biogenesis Clade Generator readme~~~

This program generates a historic clade diagram based on the backups of a biogeneis save. To use it, have a folder with
the desired world's backups ready. When starting a new world, a backup interval of 5-20 typically works best.



How to Run
------------------------------------------------------------------------------------------------------------------------
On Windows: cladegenerator.exe
With Python: cladegenerator.py (Dependencies: javaobj-py3, pyglet, Pillow)


Basic Usage
------------------------------------------------------------------------------------------------------------------------
Select the desired world folder in the file browser popup. Follow any other prompts that come up, then the generator
will work its magic. When finished, it will output one or more image files.

All relevant files are placed in <world directory>/clade. Images are saved to the output folder, and the configuration
can be set in config.ini.


Config
------------------------------------------------------------------------------------------------------------------------
The clade/config.ini file is created when the world's folder is first run. Various parameters can be configured by
editing clade.ini in a text editor.

You may also edit the config.ini file contained in this program's directory. This will set the default values for new
config files created.



This program is very early in devleopment. Expect potential bugs and crashes. More features to come.

GitHub: https://github.com/xyzfridge/BiogenesisCladeGenerator
Biogenesis Discord server: https://discord.gg/vw63CZPA3g
