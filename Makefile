#---------------------------------------------------------------------------------------------------------------------
# Pocket of Warcraft - Butano project Makefile.
#
# All art is generated from code by tools/gen_assets.py (no image files), so the graphics folder is empty and the
# generated C++ headers are written to build_gen/ before every build.
#---------------------------------------------------------------------------------------------------------------------
TARGET      	:=  pocket-of-warcraft
BUILD       	:=  build
LIBBUTANO   	:=  butano/butano
PYTHON      	:=  python3
SOURCES     	:=  src
INCLUDES    	:=  include build_gen
DATA        	:=
GRAPHICS    	:=  graphics
AUDIO       	:=  audio
AUDIOBACKEND	:=  null
AUDIOTOOL		:=
DMGAUDIO    	:=  dmg_audio
DMGAUDIOBACKEND	:=  default
ROMTITLE    	:=  POCKETOFWOW
ROMCODE     	:=  PWOW
USERFLAGS   	:=  -DBN_CFG_SPRITES_MAX_SORT_LAYERS=128
USERCXXFLAGS	:=
USERASFLAGS 	:=
USERLDFLAGS 	:=
USERLIBDIRS 	:=
USERLIBS    	:=
DEFAULTLIBS 	:=
STACKTRACE		:=
USERBUILD   	:=  build_gen
EXTTOOL     	:=  $(PYTHON) -B tools/gen_assets.py build_gen

ifndef LIBBUTANOABS
	export LIBBUTANOABS	:=	$(realpath $(LIBBUTANO))
endif

include $(LIBBUTANOABS)/butano.mak
