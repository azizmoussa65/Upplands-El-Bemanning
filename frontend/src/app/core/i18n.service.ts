import { Injectable, signal } from '@angular/core';

export type Lang = 'en' | 'sv';

const STORAGE_KEY = 'lang';

// Couverture actuelle: navigation, connexion, parametres. Les autres pages
// (leads, campagnes, tableau de bord...) restent en anglais pour l'instant -
// a etendre au besoin en suivant le meme schema de cles.
const DICTIONARY: Record<string, { en: string; sv: string }> = {
  'nav.dashboard': { en: 'Dashboard', sv: 'Översikt' },
  'nav.leads': { en: 'Leads', sv: 'Leads' },
  'nav.campaigns': { en: 'Campaigns', sv: 'Kampanjer' },
  'nav.users': { en: 'Users', sv: 'Användare' },
  'nav.settings': { en: 'Settings', sv: 'Inställningar' },
  'nav.logout': { en: 'Logout', sv: 'Logga ut' },

  'login.subtitle': { en: 'Lead prospecting platform', sv: 'Plattform för leadsprospektering' },
  'login.username': { en: 'Username', sv: 'Användarnamn' },
  'login.password': { en: 'Password', sv: 'Lösenord' },
  'login.signIn': { en: 'Sign in', sv: 'Logga in' },
  'login.invalidCredentials': { en: 'Invalid credentials', sv: 'Fel användarnamn eller lösenord' },

  'settings.title': { en: 'Settings', sv: 'Inställningar' },
  'settings.subtitle': { en: 'API keys and search preferences', sv: 'API-nycklar och sökinställningar' },
  'settings.appearance': { en: 'Appearance', sv: 'Utseende' },
  'settings.theme': { en: 'Theme', sv: 'Tema' },
  'settings.light': { en: 'Light', sv: 'Ljust' },
  'settings.dark': { en: 'Dark', sv: 'Mörkt' },
  'settings.language': { en: 'Language', sv: 'Språk' },
  'settings.save': { en: 'Save', sv: 'Spara' }
};

@Injectable({ providedIn: 'root' })
export class I18nService {
  readonly lang = signal<Lang>(this.readStored());

  setLang(lang: Lang): void {
    this.lang.set(lang);
    localStorage.setItem(STORAGE_KEY, lang);
  }

  t(key: string): string {
    const entry = DICTIONARY[key];
    if (!entry) return key;
    return entry[this.lang()];
  }

  private readStored(): Lang {
    return localStorage.getItem(STORAGE_KEY) === 'sv' ? 'sv' : 'en';
  }
}
