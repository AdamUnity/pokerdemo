import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, GameState
from .poker import GraPoker


class PokerConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.kod = self.scope['url_route']['kwargs']['kod']
        self.group_name = f'pokoj_{self.kod}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        w_pokoju = await self.czy_gracz_w_pokoju()
        if not w_pokoju:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Wyślij aktualny stan gry jeśli gra już trwa
        gra = await self.pobierz_aktualny_stan()
        if gra:
            await self.send(text_data=json.dumps({
                'typ': 'stan_gry',
                'stan': gra.stan_dla_gracza(self.user.username),
            }))

        await self.channel_layer.group_send(self.group_name, {
            'type': 'gracz_dolaczyl',
            'username': self.user.username,
        })

    async def disconnect(self, close_code):
        if not hasattr(self, 'group_name'):
            return

        await self.channel_layer.group_send(self.group_name, {
            'type': 'gracz_odszedl',
            'username': self.user.username,
        })

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        typ = data.get('typ')

        if typ == 'czat':
            await self.channel_layer.group_send(self.group_name, {
                'type': 'wiadomosc_czat',
                'username': self.user.username,
                'tresc': data.get('tresc', '')[:200],
            })

        elif typ == 'start_gry':
            await self.obsluz_start()

        elif typ == 'fold':
            await self.obsluz_akcje('fold')

        elif typ == 'check':
            await self.obsluz_akcje('check')

        elif typ == 'call':
            await self.obsluz_akcje('call')

        elif typ == 'raise':
            await self.obsluz_akcje('raise', kwota=int(data.get('kwota', 0)))

    async def obsluz_start(self):
        if not await self.czy_jest_hostem():
            await self.send_blad('Tylko host może rozpocząć grę.')
            return
        if not await self.czy_wystarczy_graczy():
            await self.send_blad('Potrzeba co najmniej 2 graczy.')
            return

        gra = await self.stworz_gre()
        await self.rozeslij_stan_gry(gra)

        await self.channel_layer.group_send(self.group_name, {
            'type': 'wiadomosc_czat',
            'username': 'System',
            'tresc': 'Gra się rozpoczyna! Powodzenia.',
        })

    async def obsluz_akcje(self, akcja, kwota=0):
        gra, blad = await self.wykonaj_akcje(akcja, kwota)
        if blad:
            await self.send_blad(blad)
            return
        await self.rozeslij_stan_gry(gra)

        if gra.czy_skonczona:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'wiadomosc_czat',
                'username': 'System',
                'tresc': f'Runda zakończona! Wygrywa {gra.zwyciezca} ({gra.uklady.get(gra.zwyciezca, "")}).',
            })
            await self.rozlicz_punkty(gra)

    async def rozeslij_stan_gry(self, gra):
        gracze = await self.pobierz_graczy()
        for gracz in gracze:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'aktualizacja_stanu',
                'username_docelowy': gracz['username'],
                'stan': gra.stan_dla_gracza(gracz['username']),
            })

    async def gracz_dolaczyl(self, event):
        gracze = await self.pobierz_graczy()
        await self.send(text_data=json.dumps({
            'typ': 'gracz_dolaczyl',
            'username': event['username'],
            'gracze': gracze,
        }))

    async def gracz_odszedl(self, event):
        gracze = await self.pobierz_graczy()
        await self.send(text_data=json.dumps({
            'typ': 'gracz_odszedl',
            'username': event['username'],
            'gracze': gracze,
        }))

    async def wiadomosc_czat(self, event):
        await self.send(text_data=json.dumps({
            'typ': 'czat',
            'username': event['username'],
            'tresc': event['tresc'],
        }))

    async def aktualizacja_stanu(self, event):
        if event['username_docelowy'] == self.user.username:
            await self.send(text_data=json.dumps({
                'typ': 'stan_gry',
                'stan': event['stan'],
            }))

    async def send_blad(self, komunikat):
        await self.send(text_data=json.dumps({
            'typ': 'blad',
            'komunikat': komunikat,
        }))

    @database_sync_to_async
    def czy_gracz_w_pokoju(self):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            return pokoj.gracze.filter(pk=self.user.pk).exists()
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def czy_jest_hostem(self):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            return pokoj.host == self.user
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def czy_wystarczy_graczy(self):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            return pokoj.gracze.count() >= 2
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def pobierz_graczy(self):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            return [{'username': g.username, 'punkty': g.points} for g in pokoj.gracze.all()]
        except Room.DoesNotExist:
            return []

    @database_sync_to_async
    def pobierz_aktualny_stan(self):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            game_state = GameState.objects.get(pokoj=pokoj)
            return game_state.get_stan()
        except (Room.DoesNotExist, GameState.DoesNotExist):
            return None

    @database_sync_to_async
    def stworz_gre(self):
        pokoj = Room.objects.get(kod=self.kod, aktywna=True)
        gracze_usernames = list(pokoj.gracze.values_list('username', flat=True))
        gra = GraPoker(gracze_usernames)
        GameState.objects.update_or_create(
            pokoj=pokoj,
            defaults={'stan_json': __import__('json').dumps(gra.do_slownika())}
        )
        return gra

    @database_sync_to_async
    def wykonaj_akcje(self, akcja, kwota=0):
        try:
            pokoj = Room.objects.get(kod=self.kod, aktywna=True)
            game_state = GameState.objects.get(pokoj=pokoj)
            gra = game_state.get_stan()
        except (Room.DoesNotExist, GameState.DoesNotExist):
            return None, 'Gra nie istnieje.'

        username = self.user.username

        if akcja == 'fold':
            ok, msg = gra.fold(username)
        elif akcja == 'check':
            ok, msg = gra.check(username)
        elif akcja == 'call':
            ok, msg = gra.call(username)
        elif akcja == 'raise':
            ok, msg = gra.raise_bet(username, kwota)
        else:
            return None, 'Nieznana akcja.'

        if not ok:
            return None, msg

        game_state.set_stan(gra)
        return gra, None

    @database_sync_to_async
    def rozlicz_punkty(self, gra):
        from accounts.models import Player
        pokoj = Room.objects.get(kod=self.kod)

        for username, wydano in gra.zuzyty_stos.items():
            try:
                gracz = Player.objects.get(username=username)
                gracz.points -= wydano
                gracz.save()
            except Player.DoesNotExist:
                pass

        if gra.zwyciezca:
            try:
                zwyciezca = Player.objects.get(username=gra.zwyciezca)
                zwyciezca.points += gra.pula
                zwyciezca.save()
            except Player.DoesNotExist:
                pass