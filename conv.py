# Geneva Bot
# Teva Keo - Crea DEV4 2020

import logging
import requests
import sys
import math
import time
import json

bot_token = sys.argv[1]

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

DIVERTISSEMENT_CHOICE, DIVERTISSEMENT_SELECT, RESTAURANT_VALUE, SORTIE_VALUE, TRANSPORT, RECHERCHE_TRANSPORT, RECHERCHE_STOP, ETAT_TRANSPORT  = range(8)

# Functions

# Start

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Sortir 🌆','Restaurants 🍖']]

    update.message.reply_text(
        'Bonjour 😀 ! Merci de faire appel à mes services pour vous divertir !\n'
        'Pour mettre fin à notre discussion vous pouvez utiliser la commande 🛑 /fin à tout moment.\n\n'
        'Pour accèder à nos infos transports utilisez la commande 🚌 /transport\n\n'
        'Pour revenir au menu vous pouvez utiliser la commande 🏡 /menu !\n\n'
        'Dites-moi le type de divertissement qui vous intéresse !',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return DIVERTISSEMENT_CHOICE

# Common Functions

def menu(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Sortir 🌆','Restaurants 🍖']]

    update.message.reply_text(
        'Dites-moi le type de divertissement qui vous intéresse !',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return DIVERTISSEMENT_CHOICE

def call_gvabot(path):
    url = "https://tova.dev/crea/python/gvabot/places?" + path.lower()
    result = requests.get(url)
    return result.json()

def appeler_opendata(path):
    url = "https://transport.opendata.ch/v1/" + path
    result = requests.get(url)
    return result.json()

def show_places(places, update):
    response = "🌆 Voici les 3 lieux les plus populaires du moment : 🌆\n\n"

    for place in places['locations']:
        response = response + "- 🎈" + place['nom'] + "🎈\n Horaires :" + place['horaires'] + "\n" + place['url'] + "\n"
        if place['prochaine_event'] is not None:
            response = response + "🥳 Evènement spécial : " + place['prochaine_event'] + "\n"
        response = response + "\n"
            
    update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())

    reply_keyboard = [['Oui','Non','Menu 🏡']]

    update.message.reply_text(
        'Souhaitez-vous consulter les transports disponibles afin de s\'y rendre ?\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

def show_restaurants(restaurants, update):
    response = "🍖 Voici les 3 restaurants que nous avons trouvés pour vous : 🍖\n\n"

    for restaurant in restaurants['locations']:
        response = response + "- 🎈" + restaurant['nom'] + "🎈\n Horaires : " + restaurant['horaires'] + ' \n Menu : ' + restaurant['url'] + "\n\n"

    update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())

    reply_keyboard = [['Oui','Non','Menu 🏡']]

    update.message.reply_text(
        'Souhaitez-vous consulter les transports disponibles afin de s\'y rendre ?\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

def afficher_arrets(arrets, update):
    for arret in arrets['stations']:
        if arret['id'] is not None:
            update.message.reply_text("/stop" + arret['id'] + " - " + arret['name'] + "")

def calculer_temps(timestamp):
    seconds = timestamp - time.time()
    minutes = seconds / 60
    minutes = math.floor(minutes)

    if minutes < 0:
        return "Trop tard"

    if (minutes < 3):
        return "Presque parti"

    return "{} min".format(minutes)

# User Interactions

def select_restaurant(update: Update, context: CallbackContext) -> int:

    reply_keyboard = [['Italien 🇮🇹','Asiatique 🍱', 'Gastronomique 🍽']]

    update.message.reply_text(
        'Très bien ! Dans quel type de réstaurant désirez-vous aller manger ?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return RESTAURANT_VALUE

def select_sortie(update: Update, context: CallbackContext) -> int:

    reply_keyboard = [['Bars 🍻','Clubs 🎊', 'Musées 🏛']]

    update.message.reply_text(
        'Très bien ! Dans quel type de lieu désirez-vous sortir ce soir ?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SORTIE_VALUE

def get_restaurant(update: Update, context: CallbackContext) -> int:
    context = update.message.text

    restau_list = call_gvabot("restaurants=" + context[:-2])
    show_restaurants(restau_list, update)

    return TRANSPORT

def get_sortie(update: Update, context: CallbackContext) -> int:
    context = update.message.text

    places_list = call_gvabot(context[:-2])
    show_places(places_list, update)

    return TRANSPORT

# Transport second handler

def message_transport(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Bonjour, veuillez m'envoyer votre localisation (en texte ou en pièce jointe)")
    return ETAT_TRANSPORT

def rechercher_par_localisation(update: Update, context: CallbackContext) -> None:
    location = update.message.location
    arrets = appeler_opendata("locations?x={}&y={}".format(location.longitude, location.latitude))
    afficher_arrets(arrets, update)
    return ETAT_TRANSPORT

def rechercher_par_nom(update: Update, context: CallbackContext) -> None:
    arrets = appeler_opendata("locations?query=" + update.message.text)
    afficher_arrets(arrets, update)
    return ETAT_TRANSPORT

def afficher_horaires(update: Update, context: CallbackContext) -> None:
    arret_id = update.message.text[5:]
    prochains_departs = appeler_opendata("stationboard?id={}&limit=10".format(arret_id))

    reponse = "Voici les prochains départs:\n\n"

    for depart in prochains_departs["stationboard"]:
        stop = depart['stop']
        reponse = reponse + calculer_temps(stop['departureTimestamp']) + ' ' + depart['number'] + " -> " + depart['to'] + "\n"

    reponse = reponse + "\nPour actualiser: /stop{}".format(arret_id)
    update.message.reply_text(reponse)
    return ETAT_TRANSPORT

# Stop Function

def fin(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("La conversation avec %s a pris fin.", user.first_name)
    update.message.reply_text(
        'Merci d\'avoir fait appel à mes services ! N\'hésitez pas à revenir quand vous le souhaitez :) !', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# Main Running Function

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with for divertissements
    conv_handler_gvabot = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DIVERTISSEMENT_CHOICE: [
                MessageHandler(Filters.regex('^(Restaurants)'), select_restaurant),
                MessageHandler(Filters.regex('^(Sortir)'), select_sortie),
            ],
            RESTAURANT_VALUE: [
                MessageHandler(Filters.regex('^(Asiatique|Italien|Gastronomique)'), get_restaurant),
            ],
            SORTIE_VALUE: [
                MessageHandler(Filters.regex('^(Bars|Clubs|Musées)'), get_sortie),
            ],
            TRANSPORT: [
                MessageHandler(Filters.regex('^(Oui)'), message_transport),
                MessageHandler(Filters.regex('^(Non)'), fin),
                MessageHandler(Filters.regex('^(Menu)'), menu),
            ],
            RECHERCHE_TRANSPORT: [
                MessageHandler(Filters.text, rechercher_par_nom),
                MessageHandler(Filters.command, afficher_horaires)
            ]
        },
        fallbacks=[
            CommandHandler('fin', fin),
            CommandHandler('menu', menu)
            ],
    )

    # Add conversation handler with for transports
    conv_handler_transport = ConversationHandler(
        entry_points=[CommandHandler('transport', message_transport)],
        states={
            ETAT_TRANSPORT: [
                CommandHandler('fin', fin),
                MessageHandler(Filters.location, rechercher_par_localisation),
                MessageHandler(Filters.command, afficher_horaires),
                MessageHandler(Filters.text, rechercher_par_nom),
            ],
        },
        fallbacks=[
            CommandHandler('fin', fin),
            CommandHandler('start', start),
        ],
    )

    # Link handlers
    dispatcher.add_handler(conv_handler_gvabot)
    dispatcher.add_handler(conv_handler_transport)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()

if __name__ == '__main__':
    main()