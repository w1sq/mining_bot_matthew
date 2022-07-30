import aiogram
from config import Config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from db.storage import UserStorage, User
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
import typing
class TG_Bot():
    def __init__(self, user_storage: UserStorage):
        self._user_storage:UserStorage = user_storage
        self._bot:aiogram.Bot = aiogram.Bot(token=Config.TGBOT_API_KEY)
        self._storage:MemoryStorage = MemoryStorage()
        self._dispatcher:aiogram.Dispatcher = aiogram.Dispatcher(self._bot, storage=self._storage)
        self._disable_web_page:bool = True
        self._accounts_in_process_pool = {}
        self._create_keyboards()

    async def init(self) :
        self._init_handler()

    async def start(self):
        print('Bot has started')
        await self._dispatcher.start_polling()
    
    async def _show_menu(self, message:aiogram.types.Message , user:User):
        match user.role:
            case User.USER:
                local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
                .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                    .row(KeyboardButton('❓️ Вопрос-ответ'), KeyboardButton('✉️ Поддержка'))
                if user.access:
                    local_keyb.row(KeyboardButton("↙️ Скачать программу"))
                else: 
                    local_keyb.row(KeyboardButton("✅ Купить программу"))
                await message.answer('Выберите интересующий вас пункт навигации: для пользователя', reply_markup=local_keyb.row(KeyboardButton(f"✨ Генерировать фразу ({user.phrases_limit})")))
            case User.ADMIN:
                local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('↕️ Админка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
                await message.answer('Выберите интересующий вас пункт навигации: для админа', reply_markup=local_keyb.row(KeyboardButton(f"✨ Генерировать фразу ({user.phrases_limit})")))

    async def _check_subscription(self, message:aiogram.types.Message, user:User):
        if user.access:
            await message.answer(text='✅ Свою часть сделки вы выполнили, спасибо! Хотите начать обучение?',reply_markup=self._checked_subscription_keyboard_access)
        else:
            await message.answer(text='✅ Свою часть сделки вы выполнили, спасибо! Хотите начать обучение?',reply_markup=self._checked_subscription_keyboard)

    async def _start_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Шаг 1"))
        await message.answer(text='Как и договаривались, я научу тебя майнить криптокошельки с балансом на своём мобильном устройстве.\n\nПоверь, это только на первый взгляд кажется сложным и непонятным, а по факту это проще, чем зарегистрироваться в одноклассниках.\n\nВнимательно следуй инструкциям.\nУ тебя всё получится  🚀',reply_markup=reply_markup)

    async def _step2_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я создал кошелёк"))
        await message.answer(text='Если ты никогда не имел дело с криптовалютой, то тебе стоит пройти весь путь от А до Я. Для начала давай заведём тебе собственный холодный кошелек. Нужен он всего лишь для того, чтобы на практике понять, как работает блокчейн.\n\nПосле установки:\n\n1. Выбираете "Создать новый кошелек"\n2. Придумываете и запоминаете пин-код\n3. Ставите галочку "Я понимаю, что если я потеряю секретную фразу, я потеряю доступ к своему кошельку"\n4. Записываете секретную фразу в блокнот и подтверждаете её',reply_markup=reply_markup)
        download_links_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Play Market', url='https://play.google.com/store/apps/details?id=com.wallet.crypto.trustapp')).row(InlineKeyboardButton(text='App Store', url='https://apps.apple.com/app/apple-store/id1288339409?mt=8'))
        await message.answer(text='Ссылки для скачивания:', reply_markup=download_links_keyboard)

    async def _step3_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✨ Сгенерировать фразу"))
        await message.answer(text='Отлично! Ты зарегистрировал свой крипто-кошелек.\n\nПри регистрации вы не указывали свои паспортные данные, номер телефона или адрес электронной почты.\nПричиной тому — анонимность и децентрализованость сетей блокчейна. Единственным доказательством того, что этот кошелек и деньги на нём ваши — секретная фраза.\n\nТут мы и подошли к сути нашего проекта: мы занимаемся тем, что генерируем такие же фразы и восстанавливаем доступ к случайным  кошелькам.\n\nДавай попробуем?',reply_markup=reply_markup)

    async def _step4_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Готово"))
        await message.answer("Тут будет фраза")
        await message.answer(text='↗️↗️↗️↗️↗️↗️↗️↗️↗️↗️\n\nЭта секретная фраза называется мнемонической или seed фразой\nОна состоит из 12 слов из словаря Bip39 (https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt) в котором находится 2048 слов.\n\nМы знаем алгоритм построения таких фраз и готовы ежедневно генерировать по 10 фраз для вас. Проверяй, что хранится на том кошельке:\n\n1. Скопируйте фразу сообщением выше\n2. Зайди в настройки приложения Trust и нажми на "Кошельки"\n3. В правом верхнем углу нажми на плюс\n4. Выбери "У меня уже есть кошелёк"\n5. Мульти-монетный кошелек\n6. Вставить и импортировать',reply_markup=reply_markup)

    async def _step5_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Начать майнить"))
        await message.answer(text='Редко случается так, что с первого раза попадается кошелек с балансом. Твоя задача пробовать ещё и ещё до тех пор, пока что-то не найдёшь.\n\nЧтобы тебе было проще ориентироваться, держи кошелек с рабочей фразой, на которой есть баланс.\n\nvolume distance dash huge giggle vehicle solve author swallow perfect coyote useless\n\nЭто не подарок, так что даже не пытайся вывести от туда деньги.\n\nУ тебя всё равно не получится, так как на этом кошельке монеты, которые невозможно перевести, обменять или продать.',reply_markup=reply_markup)

    async def _get_support_info(self, message:aiogram.types.Message, user:User):
        await message.answer(text='⁉️ По всем вопросам связанным с продуктом - @petorlov\n\nПостарайтесь коротко и в одном сообщении изложить вопрос или проблему, с которой столкнулись, а мы рассмотрим её в ближайшее время.')

    async def _generate_phrase(self, message:aiogram.types.Message, user:User):
        if user.phrases_limit > 0:
            await self._user_storage.decrease_phrase_limit(user)
            match user.role:
                case User.USER:
                    local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
                .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                    .row(KeyboardButton('❓️ Вопрос-ответ'), KeyboardButton('✉️ Поддержка'))
                    if user.access:
                        local_keyb.row(KeyboardButton("↙️ Скачать программу"))
                    else: 
                        local_keyb.row(KeyboardButton("✅ Купить программу"))
                    await message.answer('Фраза', reply_markup=local_keyb.row(KeyboardButton(f"✨ Генерировать фразу ({user.phrases_limit-1})")))
                case User.ADMIN:
                    local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('↕️ Админка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
                    await message.answer('Фраза', reply_markup=local_keyb.row(KeyboardButton(f"✨ Генерировать фразу ({user.phrases_limit-1})")))

    async def _get_profile_info(self, message:aiogram.types.Message, user:User):
        name_dict = {False:'Отсутствует', True:'Куплен'}
        await message.answer(f"👤 Ваш профиль:\n\n├ ID: {user.id}\n├ Ваш никнейм: {message['from']['username']}\n├ Ваше имя: {message['from']['first_name']}\n├ Наличие доступа: {name_dict[user.access]}\n\n├ Реферальная ссылка:\n├ https://t.me/chance_wallet_bot?start={user.id}")

    async def _get_qa_info(self, message:aiogram.types.Message, user:User):
        qa_link_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='ВОПРОС-ОТВЕТ', url='https://telegra.ph/VOPROS-OTVET-07-13-2'))
        await message.answer(text='📑 Прочитайте статью, которую мы подготовили для вас.:', reply_markup=qa_link_keyboard)
        await message.answer(text='⁉️ Не нашли ответ на свой вопрос? - @petorlov\n\nПостарайтесь коротко и в одном сообщении изложить вопрос или проблему, с которой столкнулись, а мы рассмотрим её в ближайшее время.')

    def _init_handler(self):
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._show_menu)), commands=['start'])
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._show_menu)), text='✅ Начать майнить')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._show_menu)), text='↘️ Пропустить')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._check_subscription)), text='✅ Проверить подписку')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._start_education)), text='✨Начать обучение')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._step2_education)), text='⤵️ Шаг 1')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._step3_education)), text='⤵️ Я создал кошелёк')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._step4_education)), text='✨ Сгенерировать фразу')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._step5_education)), text='✅ Готово')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._get_support_info)), text='ℹ️ Консультация')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._get_support_info)), text='✉️ Поддержка')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._get_profile_info)), text='❤️ Профиль')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._get_qa_info)), text='❓️ Вопрос-ответ')
        self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._generate_phrase)), aiogram.dispatcher.filters.Text(startswith="✨ Генерировать фразу "))
        # self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._skip_education)), text='↘️ Пропустить')
        # self._dispatcher.register_message_handler(self._subscription_middleware(self._user_middleware(self._buy_program)), text='✅ Купить программу')
    
    def _subscription_middleware(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, *args, **kwargs):
            user:ChatMember = await self._bot.get_chat_member(chat_id=Config.channel_id, user_id=message.chat.id)
            print(user)
            if user.status in ['member', 'creator', 'administrator']:
                await func(message, *args, **kwargs)
            else:
                check_channel_subcription_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text='✅ Проверить подписку'))
                await message.answer('Для того, чтобы получить доступ к боту, тебе следует подписаться на @cryptolabv2', reply_markup=check_channel_subcription_keyboard)
                channel_subcription_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Подписаться', url='https://t.me/cryptolabv2'))
                await message.answer('Оформить подписку на канал:', reply_markup=channel_subcription_keyboard)
        return wrapper

    def _user_middleware(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, *args, **kwargs):
            user = await self._user_storage.get_by_id(message.chat.id)
            if user is None:
                user = User(
                    id = message.chat.id,
                    role = User.USER,
                    access=False,
                    phrases_limit=10
                )
                await self._user_storage.create(user)
            await func(message, user)
        return wrapper
    
    def _admin_required(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, user:User, *args, **kwargs):
            if user.role == User.ADMIN:
                await func(message, user)
        return wrapper

    def _create_keyboards(self):
        self._menu_keyboard_user = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('❓️ Вопрос-ответ'), KeyboardButton('✉️ Поддержка'))\
                    .row(KeyboardButton("✅ Купить программу"))

        self._menu_keyboard_user_access = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('✉️ Поддержка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))

        self._menu_keyboard_admin = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('❤️ Профиль'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('↕️ Админка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
        
        self._checked_subscription_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('✨Начать обучение')).row(KeyboardButton('↘️ Пропустить'))\
                .row(KeyboardButton("✅ Купить программу"))
        
        self._checked_subscription_keyboard_access = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('✨Начать обучение')).row(KeyboardButton('↘️ Пропустить'))\
                .row(KeyboardButton("↙️ Скачать программу"))
        
        self._admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Выдать доступ'),KeyboardButton('Список клиентов'))\
                .row(KeyboardButton('Количество пользователей'), KeyboardButton('Увеличить лимиты'))\
                    .row(KeyboardButton('Меню'))
