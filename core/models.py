import datetime
import io
import random
import uuid

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from django.db import models, transaction
from django.db.models import Max
from django.utils.timezone import now
from django_countries.fields import CountryField
from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords


def generate_avatar(name, bg_color, size=26, text_color=(255, 255, 255)):
    # Taille de l'image
    image_size = (size, size)
    # Taille du texte
    font_size = int(size * 0.5)

    # Initiales de l'utilisateur
    initials = "".join([part[0].upper() for part in name.split()])

    # Crée une nouvelle image avec un fond coloré
    image = Image.new('RGB', image_size, bg_color)
    draw = ImageDraw.Draw(image)

    # Charge une police de caractères
    try:
        font = ImageFont.truetype("impact.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Taille du texte
    text_width, text_height = draw.textbbox((0, 0), initials, font=font)[2:]

    # Position du texte au centre de l'image
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 2)

    # Ajoute le texte à l'image
    draw.text(position, initials, fill=text_color, font=font)

    # Sauvegarde l'image dans un buffer en mémoire
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


nationalite_choices = [
    ('Afghane', 'Afghane'),
    ('Albanaise', 'Albanaise'),
    ('Algérienne', 'Algérienne'),
    ('Allemande', 'Allemande'),
    ('Américaine', 'Américaine'),
    ('Andorrane', 'Andorrane'),
    ('Angolaise', 'Angolaise'),
    ('Antiguaise-et-Barbudienne', 'Antiguaise-et-Barbudienne'),
    ('Argentine', 'Argentine'),
    ('Arménienne', 'Arménienne'),
    ('Australienne', 'Australienne'),
    ('Autrichienne', 'Autrichienne'),
    ('Azerbaïdjanaise', 'Azerbaïdjanaise'),
    ('Bahamienne', 'Bahamienne'),
    ('Bahreïnienne', 'Bahreïnienne'),
    ('Bangladaise', 'Bangladaise'),
    ('Barbadiènne', 'Barbadiènne'),
    ('Bélarusse', 'Bélarusse'),
    ('Belge', 'Belge'),
    ('Bélizienne', 'Bélizienne'),
    ('Béninoise', 'Béninoise'),
    ('Bhoutanaise', 'Bhoutanaise'),
    ('Birmane', 'Birmane'),
    ('Bolivienne', 'Bolivienne'),
    ('Bosniaque', 'Bosniaque'),
    ('Botswanéenne', 'Botswanéenne'),
    ('Brésilienne', 'Brésilienne'),
    ('Britannique', 'Britannique'),
    ('Brunéienne', 'Brunéienne'),
    ('Bulgare', 'Bulgare'),
    ('Burkinabè', 'Burkinabè'),
    ('Burundaise', 'Burundaise'),
    ('Cambodgienne', 'Cambodgienne'),
    ('Camerounaise', 'Camerounaise'),
    ('Canadienne', 'Canadienne'),
    ('Cap-Verdienne', 'Cap-Verdienne'),
    ('Centrafricaine', 'Centrafricaine'),
    ('Chilienne', 'Chilienne'),
    ('Chinoise', 'Chinoise'),
    ('Chypriote', 'Chypriote'),
    ('Colombienne', 'Colombienne'),
    ('Comorienne', 'Comorienne'),
    ('Congolaise (Congo-Brazzaville)', 'Congolaise (Congo-Brazzaville)'),
    ('Congolaise (Congo-Kinshasa)', 'Congolaise (Congo-Kinshasa)'),
    ('Costaricaine', 'Costaricaine'),
    ('Croate', 'Croate'),
    ('Cubaine', 'Cubaine'),
    ('Danoise', 'Danoise'),
    ('Djiboutienne', 'Djiboutienne'),
    ('Dominicaine', 'Dominicaine'),
    ('Dominicain(e)', 'Dominicain(e)'),
    ('Égyptienne', 'Égyptienne'),
    ('Émirienne', 'Émirienne'),
    ('Équatorienne', 'Équatorienne'),
    ('Érythréenne', 'Érythréenne'),
    ('Espagnole', 'Espagnole'),
    ('Estonienne', 'Estonienne'),
    ('Éthiopienne', 'Éthiopienne'),
    ('Fidjienne', 'Fidjienne'),
    ('Finlandaise', 'Finlandaise'),
    ('Française', 'Française'),
    ('Gabonaise', 'Gabonaise'),
    ('Gambienne', 'Gambienne'),
    ('Géorgienne', 'Géorgienne'),
    ('Ghanéenne', 'Ghanéenne'),
    ('Grenadienne', 'Grenadienne'),
    ('Guatémaltèque', 'Guatémaltèque'),
    ('Guinéenne', 'Guinéenne'),
    ('Guinéenne (Guinée-Bissau)', 'Guinéenne (Guinée-Bissau)'),
    ('Guyanienne', 'Guyanienne'),
    ('Haïtienne', 'Haïtienne'),
    ('Hellénique (Greque)', 'Hellénique (Greque)'),
    ('Hondurienne', 'Hondurienne'),
    ('Hongroise', 'Hongroise'),
    ('Indienne', 'Indienne'),
    ('Indonésienne', 'Indonésienne'),
    ('Irakienne', 'Irakienne'),
    ('Iranienne', 'Iranienne'),
    ('Irlandaise', 'Irlandaise'),
    ('Islandaise', 'Islandaise'),
    ('Israélienne', 'Israélienne'),
    ('Italienne', 'Italienne'),
    ('Ivoirienne', 'Ivoirienne'),
    ('Jamaïcaine', 'Jamaïcaine'),
    ('Japonaise', 'Japonaise'),
    ('Jordanienne', 'Jordanienne'),
    ('Kazakhe', 'Kazakhe'),
    ('Kényane', 'Kényane'),
    ('Kirghize', 'Kirghize'),
    ('Kiribatienne', 'Kiribatienne'),
    ('Koweïtienne', 'Koweïtienne'),
    ('Laotienne', 'Laotienne'),
    ('Lettone', 'Lettone'),
    ('Libanaise', 'Libanaise'),
    ('Libérienne', 'Libérienne'),
    ('Libyenne', 'Libyenne'),
    ('Liechtensteinoise', 'Liechtensteinoise'),
    ('Lituanienne', 'Lituanienne'),
    ('Luxembourgeoise', 'Luxembourgeoise'),
    ('Macédonienne', 'Macédonienne'),
    ('Malaisienne', 'Malaisienne'),
    ('Malawienne', 'Malawienne'),
    ('Maldivienne', 'Maldivienne'),
    ('Malgache', 'Malgache'),
    ('Malienne', 'Malienne'),
    ('Maltaise', 'Maltaise'),
    ('Marocaine', 'Marocaine'),
    ('Maréchalienne', 'Maréchalienne'),
    ('Mauricienne', 'Mauricienne'),
    ('Mauritanienne', 'Mauritanienne'),
    ('Mexicaine', 'Mexicaine'),
    ('Micronésienne', 'Micronésienne'),
    ('Moldave', 'Moldave'),
    ('Monégasque', 'Monégasque'),
    ('Mongole', 'Mongole'),
    ('Monténégrine', 'Monténégrine'),
    ('Mozambicaine', 'Mozambicaine'),
    ('Namibienne', 'Namibienne'),
    ('Nauruane', 'Nauruane'),
    ('Népalaise', 'Népalaise'),
    ('Nicaraguayenne', 'Nicaraguayenne'),
    ('Nigérienne', 'Nigérienne'),
    ('Nigériane', 'Nigériane'),
    ('Norvégienne', 'Norvégienne'),
    ('Néo-Zélandaise', 'Néo-Zélandaise'),
    ('Omanaise', 'Omanaise'),
    ('Ougandaise', 'Ougandaise'),
    ('Ouzbèke', 'Ouzbèke'),
    ('Pakistanaise', 'Pakistanaise'),
    ('Palaosienne', 'Palaosienne'),
    ('Palestinienne', 'Palestinienne'),
    ('Panaméenne', 'Panaméenne'),
    ('Papouane-Néo-Guinéenne', 'Papouane-Néo-Guinéenne'),
    ('Paraguayenne', 'Paraguayenne'),
    ('Néerlandaise', 'Néerlandaise'),
    ('Péruvienne', 'Péruvienne'),
    ('Philippine', 'Philippine'),
    ('Polonaise', 'Polonaise'),
    ('Portugaise', 'Portugaise'),
    ('Qatarienne', 'Qatarienne'),
    ('Roumaine', 'Roumaine'),
    ('Russe', 'Russe'),
    ('Rwandaise', 'Rwandaise'),
    ('Saint-Christophoro-Névicienne', 'Saint-Christophoro-Névicienne'),
    ('Saint-Lucienne', 'Saint-Lucienne'),
    ('Saint-Marinaise', 'Saint-Marinaise'),
    ('Saint-Vincentaise-et-Grenadine', 'Saint-Vincentaise-et-Grenadine'),
    ('Salomonaise', 'Salomonaise'),
    ('Salvadorienne', 'Salvadorienne'),
    ('Samoane', 'Samoane'),
    ('Santoméenne', 'Santoméenne'),
    ('Saoudienne', 'Saoudienne'),
    ('Sénégalaise', 'Sénégalaise'),
    ('Serbe', 'Serbe'),
    ('Seychelloise', 'Seychelloise'),
    ('Sierra-Léonaise', 'Sierra-Léonaise'),
    ('Singapourienne', 'Singapourienne'),
    ('Slovaque', 'Slovaque'),
    ('Slovène', 'Slovène'),
    ('Somalienne', 'Somalienne'),
    ('Soudanaise', 'Soudanaise'),
    ('Sud-Africaine', 'Sud-Africaine'),
    ('Sud-Soudanaise', 'Sud-Soudanaise'),
    ('Sri-Lankaise', 'Sri-Lankaise'),
    ('Suédoise', 'Suédoise'),
    ('Suisse', 'Suisse'),
    ('Surinamaise', 'Surinamaise'),
    ('Swazie', 'Swazie'),
    ('Syrienne', 'Syrienne'),
    ('Tadjike', 'Tadjike'),
    ('Tanzanienne', 'Tanzanienne'),
    ('Tchadienne', 'Tchadienne'),
    ('Tchèque', 'Tchèque'),
    ('Thaïlandaise', 'Thaïlandaise'),
    ('Timoraise', 'Timoraise'),
    ('Togolaise', 'Togolaise'),
    ('Tonguienne', 'Tonguienne'),
    ('Trinidadienne', 'Trinidadienne'),
    ('Tunisienne', 'Tunisienne'),
    ('Turkmène', 'Turkmène'),
    ('Turque', 'Turque'),
    ('Tuvaluane', 'Tuvaluane'),
    ('Ukrainienne', 'Ukrainienne'),
    ('Uruguayenne', 'Uruguayenne'),
    ('Vanuatuane', 'Vanuatuane'),
    ('Vénézuélienne', 'Vénézuélienne'),
    ('Vietnamienne', 'Vietnamienne'),
    ('Yéménite', 'Yéménite'),
    ('Zambienne', 'Zambienne'),
    ('Zimbabwéenne', 'Zimbabwéenne')
]
pays_choices = [
    ('Cote-d-Ivoire', 'Côte d\'Ivoire'),
    ('Afghanistan', 'Afghanistan'),
    ('Albania', 'Albania'),
    ('Algeria', 'Algeria'),
    ('Andorra', 'Andorra'),
    ('Angola', 'Angola'),
    ('Antigua and Barbuda', 'Antigua and Barbuda'),
    ('Argentina', 'Argentina'),
    ('Armenia', 'Armenia'),
    ('Australia', 'Australia'),
    ('Austria', 'Austria'),
    ('Azerbaijan', 'Azerbaijan'),
    ('Bahamas', 'Bahamas'),
    ('Bahrain', 'Bahrain'),
    ('Bangladesh', 'Bangladesh'),
    ('Barbados', 'Barbados'),
    ('Belarus', 'Belarus'),
    ('Belgium', 'Belgium'),
    ('Belize', 'Belize'),
    ('Benin', 'Benin'),
    ('Bhutan', 'Bhutan'),
    ('Bolivia', 'Bolivia'),
    ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),
    ('Botswana', 'Botswana'),
    ('Brazil', 'Brazil'),
    ('Brunei', 'Brunei'),
    ('Bulgaria', 'Bulgaria'),
    ('Burkina Faso', 'Burkina Faso'),
    ('Burundi', 'Burundi'),
    ('Cabo Verde', 'Cabo Verde'),
    ('Cambodia', 'Cambodia'),
    ('Cameroon', 'Cameroon'),
    ('Canada', 'Canada'),
    ('Central African Republic', 'Central African Republic'),
    ('Chad', 'Chad'),
    ('Chile', 'Chile'),
    ('China', 'China'),
    ('Colombia', 'Colombia'),
    ('Comoros', 'Comoros'),
    ('Congo (Congo-Brazzaville)', 'Congo (Congo-Brazzaville)'),
    ('Costa Rica', 'Costa Rica'),
    ('Croatia', 'Croatia'),

    ('Cuba', 'Cuba'),
    ('Cyprus', 'Cyprus'),
    ('Czechia (Czech Republic)', 'Czechia (Czech Republic)'),
    ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'),
    ('Denmark', 'Denmark'),
    ('Djibouti', 'Djibouti'),
    ('Dominica', 'Dominica'),
    ('Dominican Republic', 'Dominican Republic'),
    ('Ecuador', 'Ecuador'),
    ('Egypt', 'Egypt'),
    ('El Salvador', 'El Salvador'),
    ('Equatorial Guinea', 'Equatorial Guinea'),
    ('Eritrea', 'Eritrea'),
    ('Estonia', 'Estonia'),
    ('Eswatini (fmr. "Swaziland")', 'Eswatini (fmr. "Swaziland")'),
    ('Ethiopia', 'Ethiopia'),
    ('Fiji', 'Fiji'),
    ('Finland', 'Finland'),
    ('France', 'France'),
    ('Gabon', 'Gabon'),
    ('Gambia', 'Gambia'),
    ('Georgia', 'Georgia'),
    ('Germany', 'Germany'),
    ('Ghana', 'Ghana'),
    ('Greece', 'Greece'),
    ('Grenada', 'Grenada'),
    ('Guatemala', 'Guatemala'),
    ('Guinea', 'Guinea'),
    ('Guinea-Bissau', 'Guinea-Bissau'),
    ('Guyana', 'Guyana'),
    ('Haiti', 'Haiti'),
    ('Honduras', 'Honduras'),
    ('Hungary', 'Hungary'),
    ('Iceland', 'Iceland'),
    ('India', 'India'),
    ('Indonesia', 'Indonesia'),
    ('Iran', 'Iran'),
    ('Iraq', 'Iraq'),
    ('Ireland', 'Ireland'),
    ('Israel', 'Israel'),
    ('Italy', 'Italy'),
    ('Jamaica', 'Jamaica'),
    ('Japan', 'Japan'),
    ('Jordan', 'Jordan'),
    ('Kazakhstan', 'Kazakhstan'),
    ('Kenya', 'Kenya'),
    ('Kiribati', 'Kiribati'),
    ('Kuwait', 'Kuwait'),
    ('Kyrgyzstan', 'Kyrgyzstan'),
    ('Laos', 'Laos'),
    ('Latvia', 'Latvia'),
    ('Lebanon', 'Lebanon'),
    ('Lesotho', 'Lesotho'),
    ('Liberia', 'Liberia'),
    ('Libya', 'Libya'),
    ('Liechtenstein', 'Liechtenstein'),
    ('Lithuania', 'Lithuania'),
    ('Luxembourg', 'Luxembourg'),
    ('Madagascar', 'Madagascar'),
    ('Malawi', 'Malawi'),
    ('Malaysia', 'Malaysia'),
    ('Maldives', 'Maldives'),
    ('Mali', 'Mali'),
    ('Malta', 'Malta'),
    ('Marshall Islands', 'Marshall Islands'),
    ('Mauritania', 'Mauritania'),
    ('Mauritius', 'Mauritius'),
    ('Mexico', 'Mexico'),
    ('Micronesia', 'Micronesia'),
    ('Moldova', 'Moldova'),
    ('Monaco', 'Monaco'),
    ('Mongolia', 'Mongolia'),
    ('Montenegro', 'Montenegro'),
    ('Morocco', 'Morocco'),
    ('Mozambique', 'Mozambique'),
    ('Myanmar (formerly Burma)', 'Myanmar (formerly Burma)'),
    ('Namibia', 'Namibia'),
    ('Nauru', 'Nauru'),
    ('Nepal', 'Nepal'),
    ('Netherlands', 'Netherlands'),
    ('New Zealand', 'New Zealand'),
    ('Nicaragua', 'Nicaragua'),
    ('Niger', 'Niger'),
    ('Nigeria', 'Nigeria'),
    ('North Korea', 'North Korea'),
    ('North Macedonia', 'North Macedonia'),
    ('Norway', 'Norway'),
    ('Oman', 'Oman'),
    ('Pakistan', 'Pakistan'),
    ('Palau', 'Palau'),
    ('Palestine State', 'Palestine State'),
    ('Panama', 'Panama'),
    ('Papua New Guinea', 'Papua New Guinea'),
    ('Paraguay', 'Paraguay'),
    ('Peru', 'Peru'),
    ('Philippines', 'Philippines'),
    ('Poland', 'Poland'),
    ('Portugal', 'Portugal'),
    ('Qatar', 'Qatar'),
    ('Romania', 'Romania'),
    ('Russia', 'Russia'),
    ('Rwanda', 'Rwanda'),
    ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
    ('Saint Lucia', 'Saint Lucia'),
    ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
    ('Samoa', 'Samoa'),
    ('San Marino', 'San Marino'),
    ('Sao Tome and Principe', 'Sao Tome and Principe'),
    ('Saudi Arabia', 'Saudi Arabia'),
    ('Senegal', 'Senegal'),
    ('Serbia', 'Serbia'),
    ('Seychelles', 'Seychelles'),
    ('Sierra Leone', 'Sierra Leone'),
    ('Singapore', 'Singapore'),
    ('Slovakia', 'Slovakia'),
    ('Slovenia', 'Slovenia'),
    ('Solomon Islands', 'Solomon Islands'),
    ('Somalia', 'Somalia'),
    ('South Africa', 'South Africa'),
    ('South Korea', 'South Korea'),
    ('South Sudan', 'South Sudan'),
    ('Spain', 'Spain'),
    ('Sri Lanka', 'Sri Lanka'),
    ('Sudan', 'Sudan'),
    ('Suriname', 'Suriname'),
    ('Sweden', 'Sweden'),
    ('Switzerland', 'Switzerland'),
    ('Syria', 'Syria'),
    ('Taiwan', 'Taiwan'),
    ('Tajikistan', 'Tajikistan'),
    ('Tanzania', 'Tanzania'),
    ('Thailand', 'Thailand'),
    ('Timor-Leste', 'Timor-Leste'),
    ('Togo', 'Togo'),
    ('Tonga', 'Tonga'),
    ('Trinidad and Tobago', 'Trinidad and Tobago'),
    ('Tunisia', 'Tunisia'),
    ('Turkey', 'Turkey'),
    ('Turkmenistan', 'Turkmenistan'),
    ('Tuvalu', 'Tuvalu'),
    ('Uganda', 'Uganda'),
    ('Ukraine', 'Ukraine'),
    ('United Arab Emirates', 'United Arab Emirates'),
    ('United Kingdom', 'United Kingdom'),
    ('Etats Unies', 'Etats Unies'),
    ('Uruguay', 'Uruguay'),
    ('Uzbekistan', 'Uzbekistan'),
    ('Vanuatu', 'Vanuatu'),
    ('Vatican City', 'Vatican City'),
    ('Venezuela', 'Venezuela'),
    ('Vietnam', 'Vietnam'),
    ('Yemen', 'Yemen'),
    ('Zambia', 'Zambia'),
    ('Zimbabwe', 'Zimbabwe'),
    ('Autre', 'Autre')
]
situation_matrimoniales_choices = [
    ('Celibataire', 'Celibataire'),
    ('Concubinage', 'Concubinage'),
    ('Marie', 'Marié'),
    ('Divorce', 'Divorcé'),
    ('Veuf', 'Veuf'),
    ('Autre', 'Autre'),
]

Patient_statut_choices = [
    ('Admis', 'Admis'),
    ('Sorti', 'Sorti'),
    ('Gueris-EXEA', 'Gueris-EXEA'),
    ('Transféré-TRANSF', 'Transféré-TRANSF'),
    ('SCAM', 'SCAM'),
    ('EVADE', 'EVADE'),
    ('DCD', 'DCD'),
    ('Sous observation', 'Sous observation'),
    ('Sous traitement', 'Sous traitement'),
    ('Chirurgie programmée', 'Chirurgie programmée'),
    ('En chirurgie', 'En chirurgie'),
    ('Récupération post-opératoire', 'Récupération post-opératoire'),
    ('USI', 'Unité de soins intensifs (USI)'),
    ('Urgence', 'Urgence'),
    ('Consultation externe', 'Consultation externe'),
    ('Réhabilitation', 'Réhabilitation'),
    ('En attente de diagnostic', 'En attente de diagnostic'),
    ('Traitement en cours', 'Traitement en cours'),
    ('Suivi programmé', 'Suivi programmé'),
    ('Consultation', 'Consultation'),
    ('Sortie en attente', 'Sortie en attente'),
    ('Isolement', 'Isolement'),
    ('Ambulantoire', 'Ambulantoire'),
    ('Aucun', 'Aucun')
]

villes_choices = [
    ('Abidjan', 'Abidjan'),
    ('Yamoussoukro', 'Yamoussoukro'),
    ('Bouaké', 'Bouaké'),
    ('Daloa', 'Daloa'),
    ('Korhogo', 'Korhogo'),
    ('Man', 'Man'),
    ('San Pedro', 'San Pedro'),
    ('Divo', 'Divo'),
    ('Gagnoa', 'Gagnoa'),
    ('Abengourou', 'Abengourou'),
    ('Agboville', 'Agboville'),
    ('Grand-Bassam', 'Grand-Bassam'),
    ('Soubré', 'Soubré'),
    ('Ferkessédougou', 'Ferkessédougou'),
    ('Odienné', 'Odienné'),
    ('Séguéla', 'Séguéla'),
    ('Bingerville', 'Bingerville'),
    ('Bondoukou', 'Bondoukou'),
    ('Daoukro', 'Daoukro'),
    ('Issia', 'Issia'),
    ('Sassandra', 'Sassandra'),
    ('Tengrela', 'Tengrela'),
    ('Agnibilékrou', 'Agnibilékrou'),
    ('Anyama', 'Anyama'),
    ('Arrah', 'Arrah'),
    ('Béoumi', 'Béoumi'),
    ('Biankouma', 'Biankouma'),
    ('Bouna', 'Bouna'),
    ('Boundiali', 'Boundiali'),
    ('Dabou', 'Dabou'),
    ('Danané', 'Danané'),
    ('Duékoué', 'Duékoué'),
    ('Grand-Lahou', 'Grand-Lahou'),
    ('Guiglo', 'Guiglo'),
    ('Katiola', 'Katiola'),
    ('Lakota', 'Lakota'),
    ('Méagui', 'Méagui'),
    ('Mankono', 'Mankono'),
    ('Oumé', 'Oumé'),
    ('Sinfra', 'Sinfra'),
    ('Tiassalé', 'Tiassalé'),
    ('Touba', 'Touba'),
    ('Toumodi', 'Toumodi'),
    ('Vavoua', 'Vavoua'),
    ('Yopougon', 'Yopougon'),
    ('Zuenoula', 'Zuenoula'),
    ('Autre', 'Autre'),
]
professions_choices = [
    ('Médecin', 'Médecin'),
    ('Infirmier/Infirmière', 'Infirmier/Infirmière'),
    ('Dentiste', 'Dentiste'),
    ('Pharmacien/Pharmacienne', 'Pharmacien/Pharmacienne'),
    ('Vétérinaire', 'Vétérinaire'),
    ('Ingénieur', 'Ingénieur'),
    ('Architecte', 'Architecte'),
    ('Professeur/Professeure', 'Professeur/Professeure'),
    ('Enseignant/Enseignante', 'Enseignant/Enseignante'),
    ('Chercheur/Chercheuse', 'Chercheur/Chercheuse'),
    ('Scientifique', 'Scientifique'),
    ('Technicien/Technicienne', 'Technicien/Technicienne'),
    ('Informaticien/Informaticienne', 'Informaticien/Informaticienne'),
    ('Programmeur/Programmeuse', 'Programmeur/Programmeuse'),
    ('Développeur/Développeuse', 'Développeur/Développeuse'),
    ('Analyste', 'Analyste'),
    ('Consultant/Consultante', 'Consultant/Consultante'),
    ('Électricien/Électricienne', 'Électricien/Électricienne'),
    ('Plombier/Plombière', 'Plombier/Plombière'),
    ('Mécanicien/Mécanicienne', 'Mécanicien/Mécanicienne'),
    ('Charpentier/Charpentière', 'Charpentier/Charpentière'),
    ('Maçon/Maçonne', 'Maçon/Maçonne'),
    ('Couvreur/Couvreuse', 'Couvreur/Couvreuse'),
    ('Menuisier/Menuisière', 'Menuisier/Menuisière'),
    ('Forgeron/Forgeronne', 'Forgeron/Forgeronne'),
    ('Serrurier/Serrurière', 'Serrurier/Serrurière'),
    ('Couturier/Couturière', 'Couturier/Couturière'),
    ('Coiffeur/Coiffeuse', 'Coiffeur/Coiffeuse'),
    ('Esthéticien/Esthéticienne', 'Esthéticien/Esthéticienne'),
    ('Chef cuisinier/Chef cuisinière', 'Chef cuisinier/Chef cuisinière'),
    ('Serveur/Serveuse', 'Serveur/Serveuse'),
    ('Barman/Barmaid', 'Barman/Barmaid'),
    ('Agriculteur/Agricultrice', 'Agriculteur/Agricultrice'),
    ('Éleveur/Éleveuse', 'Éleveur/Éleveuse'),
    ('Pêcheur/Pêcheuse', 'Pêcheur/Pêcheuse'),
    ('Jardinier/Jardinière', 'Jardinier/Jardinière'),
    ('Conducteur/Conductrice', 'Conducteur/Conductrice'),
    ('Chauffeur/Chauffeuse', 'Chauffeur/Chauffeuse'),
    ('Pilote', 'Pilote'),
    ('Steward/Hôtesse de l\'air', 'Steward/Hôtesse de l\'air'),
    ('Agent de bord', 'Agent de bord'),
    ('Policier/Policière', 'Policier/Policière'),
    ('Gendarme', 'Gendarme'),
    ('Pompier', 'Pompier'),
    ('Soldat', 'Soldat'),
    ('Officier', 'Officier'),
    ('Avocat/Avocate', 'Avocat/Avocate'),
    ('Juge', 'Juge'),
    ('Notaire', 'Notaire'),
    ('Écrivain/Écrivaine', 'Écrivain/Écrivaine'),
    ('Journaliste', 'Journaliste'),
    ('Photographe', 'Photographe'),
    ('Réalisateur/Réalisatrice', 'Réalisateur/Réalisatrice'),
    ('Acteur/Actrice', 'Acteur/Actrice'),
    ('Musicien/Musicienne', 'Musicien/Musicienne'),
    ('Chanteur/Chanteuse', 'Chanteur/Chanteuse'),
    ('Danseur/Danseuse', 'Danseur/Danseuse'),
    ('Artiste peintre', 'Artiste peintre'),
    ('Sculpteur/Sculptrice', 'Sculpteur/Sculptrice'),
    ('Designer', 'Designer'),
    ('Graphiste', 'Graphiste'),
    ('Webdesigner', 'Webdesigner'),
    ('Publicitaire', 'Publicitaire'),
    ('Marketeur/Marketeuse', 'Marketeur/Marketeuse'),
    ('Comptable', 'Comptable'),
    ('Banquier/Banquière', 'Banquier/Banquière'),
    ('Assureur/Assureuse', 'Assureur/Assureuse'),
    ('Courtier/Courtière', 'Courtier/Courtière'),
    ('Gestionnaire', 'Gestionnaire'),
    ('Directeur/Directrice', 'Directeur/Directrice'),
    ('Cadre', 'Cadre'),
    ('Assistant/Assistante', 'Assistant/Assistante'),
    ('Secrétaire', 'Secrétaire'),
    ('Réceptionniste', 'Réceptionniste'),
    ('Agent d\'entretien', 'Agent d\'entretien'),
    ('Facteur/Factrice', 'Facteur/Factrice'),
    ('Livreur/Livreuse', 'Livreur/Livreuse'),
    ('Éboueur/Éboueuse', 'Éboueur/Éboueuse'),
    ('Gardien/Gardienne', 'Gardien/Gardienne'),
    ('Concierge', 'Concierge'),
    ('Bibliothécaire', 'Bibliothécaire'),
    ('Archiviste', 'Archiviste'),
    ('Documentaliste', 'Documentaliste'),
    ('Traducteur/Traductrice', 'Traducteur/Traductrice'),
    ('Interprète', 'Interprète'),
    ('Autre', 'Autre')
]
Goupe_sanguin_choices = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('Inconnu', 'Inconnu'),
]

Sexe_choices = [
    ('Homme', 'Homme'),
    ('Femme', 'Femme'),

]

communes_et_quartiers_choices = [
    ('Abobo', 'Abobo'),
    ('Adjamé', 'Adjamé'),
    ('Aboisso', 'Aboisso'),
    ('Abengourou', 'Abengourou'),
    ('Adzopé', 'Adzopé'),
    ('Agboville', 'Agboville'),
    ('Agboville', 'Agboville'),
    ('Anyama', 'Anyama'),
    ('Attécoubé', 'Attécoubé'),
    ('Bongouanou', 'Bongouanou'),
    ('Bondoukou', 'Bondoukou'),
    ('Bouaflé', 'Bouaflé'),
    ('Bouaké', 'Bouaké'),
    ('Bouna', 'Bouna'),
    ('Bonoua', 'Bonoua'),
    ('Cocody', 'Cocody'),
    ('Daloa', 'Daloa'),
    ('Divo', 'Divo'),
    ('Grand-Bassam', 'Grand-Bassam'),
    ('Grand-Lahou', 'Grand-Lahou'),
    ('Guiglo', 'Guiglo'),
    ('Korhogo', 'Korhogo'),
    ('Man', 'Man'),
    ('San Pedro', 'San Pedro'),
    ('San Pédro', 'San Pédro'),
    ('Séguéla', 'Séguéla'),
    ('Sinfra', 'Sinfra'),
    ('Soubré', 'Soubré'),
    ('Tanda', 'Tanda'),
    ('Tabou', 'Tabou'),
    ('Tingrela', 'Tingrela'),
    ('Yamoussoukro', 'Yamoussoukro'),
    ('Yopougon', 'Yopougon'),
    ('Bingerville', 'Bingerville'),
    ('Daloa', 'Daloa'),
    ('Tiassalé', 'Tiassalé'),
    ('Akan', 'Akan'),
    ('Dimbokro', 'Dimbokro'),
    ('Gagnoa', 'Gagnoa'),
    ('Dabou', 'Dabou'),
    ('Lakota', 'Lakota'),
    ('Katiola', 'Katiola'),
    ('Mankono', 'Mankono'),
    ('Niakara', 'Niakara'),
    ('Ouangolodougou', 'Ouangolodougou'),
    ('Oumé', 'Oumé'),
    ('Tiebissou', 'Tiebissou'),
    ('Danané', 'Danané'),
    ('Odienné', 'Odienné'),
    ('Tiapoum', 'Tiapoum'),
    ('Bounoua', 'Bounoua'),
    ('Bouaflé', 'Bouaflé'),
    ('Bingerville', 'Bingerville'),
    ('Kouassi-Datékro', 'Kouassi-Datékro'),
    ('Zuenoula', 'Zuenoula'),
    ('Ferkessedougou', 'Ferkessedougou'),
    ('Dabakala', 'Dabakala'),
    ('Tiebissou', 'Tiebissou'),
    ('Bingerville', 'Bingerville'),
    ('Moussoukoro', 'Moussoukoro'),
    ('Zouan-Hounien', 'Zouan-Hounien'),
    ('Vavoua', 'Vavoua'),
    ('Sikensi', 'Sikensi'),
    ('Bouna', 'Bouna'),
    ('Oberlin', 'Oberlin'),
    ('Bongouanou', 'Bongouanou'),
    ('Bocanda', 'Bocanda'),
    ('Kani', 'Kani'),
    ('Brobo', 'Brobo'),
    ('Prikro', 'Prikro'),
    ('Niakara', 'Niakara'),
    ('Dabou', 'Dabou'),
    ('Katiola', 'Katiola'),
    ('Kouibly', 'Kouibly'),
    ('Sakassou', 'Sakassou'),
    ('Tengrela', 'Tengrela'),
    ('Bouaflé', 'Bouaflé'),
    ('Gagnoa', 'Gagnoa'),
    ('Mankono', 'Mankono'),
    ('Oumé', 'Oumé'),
    ('Grand Lahou', 'Grand Lahou'),
    ('Ouangolodougou', 'Ouangolodougou'),
    ('Kouassi-Kouassikro', 'Kouassi-Kouassikro'),
    ('Sassandra', 'Sassandra'),
    ('Autre', 'Autre'),
]


def get_random_code() -> str:
    return str(datetime.date.today().year)[2:] + str(random.randint(0000, 999999))


# def get_incremental_code() -> str:
#     current_year = datetime.date.today().year
#     current_year_short = str(current_year)[2:]
#
#     # Get the latest patient code for the current year
#     latest_patient = Patient.objects.filter(code_vih__startswith=current_year_short).aggregate(Max('code_vih'))[
#         'code_vih__max']
#
#     if latest_patient:
#         # Extract the numeric part and increment it
#         latest_number = int(latest_patient.split('-')[1])
#         new_number = latest_number + 1
#     else:
#         # If no patient for the current year, start with 1
#         new_number = 1
#
#     # Format the new number with leading zeros
#     new_code = f"{current_year_short}-{new_number:04d}"
#     return new_code
#
def get_incremental_code() -> str:
    current_year = datetime.date.today().year
    current_year_short = str(current_year)[2:]

    # Use a transaction to ensure atomicity and uniqueness
    with transaction.atomic():
        # Lock the table to prevent race conditions
        latest_patient = Patient.objects.select_for_update().filter(code_vih__startswith=current_year_short
                                                                    ).aggregate(Max('code_vih'))['code_vih__max']

        if latest_patient:
            # Extract the numeric part and increment it
            latest_number = int(latest_patient.split('-')[1])
            new_number = latest_number + 1
        else:
            # If no patient for the current year, start with 1
            new_number = 1

        # Format the new number with leading zeros
        new_code = f"{current_year_short}-{new_number:04d}"

    return new_code


def qlook():
    qlook = ("QL" + str(random.randrange(0, 999999999, 1)) + "URAP")
    return qlook


# class Localite(models.Model):
#     nom = models.CharField(max_length=255)
#     code = models.CharField(max_length=50, null=True, blank=True)  # Si des codes spécifiques existent
#     type = models.CharField(max_length=50, null=True, blank=True)  # Par exemple, ville, commune, village
#     region = models.CharField(max_length=255, null=True, blank=True)  # Si applicable
#     geojson = models.JSONField(null=True, blank=True, )
#
#     def __str__(self):
#         return self.nom


# Create your models here.
class Location(models.Model):
    contry = CountryField()
    ville = models.CharField(max_length=225, null=True, blank=True)
    commune = models.CharField(max_length=225, null=True, blank=True)
    quartier = models.CharField(max_length=225, null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True)
    current_location = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.commune}, {self.contry}"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.created_at


class Service(models.Model):
    nom = models.CharField(max_length=225, null=True, blank=True)
    icon = models.CharField(max_length=225, null=True, blank=True, default='fa-solid fa-virus')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom

    # @property
    # def consultation_count(self):
    #     return self.consultation_set.count()


class ServiceSubActivity(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, related_name='subactivities')
    nom = models.CharField(max_length=225, null=True, blank=True)
    icon = models.CharField(max_length=225, null=True, blank=True)

    def __str__(self):
        return f'{self.nom} - {self.service}'


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee", )
    qlook_id = models.CharField(default=qlook, unique=True, editable=False, max_length=100)
    gender = models.CharField(choices=Sexe_choices, max_length=100, null=True, blank=True, )
    situation_matrimoniale = models.CharField(choices=situation_matrimoniales_choices, max_length=100, null=True,
                                              blank=True, )
    nbr_enfants = models.IntegerField(null=True, blank=True, default='20')
    persone_ref_noms = models.CharField(null=True, blank=True, max_length=100, default='Jean Kouame')
    persone_ref_contact = models.CharField(null=True, blank=True, max_length=100, default='05 00 05 00 05')
    # persone_ref_type = models.CharField(choices=REF_CHOICES, max_length=100, null=True, blank=True, )
    num_cnps = models.CharField(null=True, blank=True, max_length=100, default='CNPS00000000')
    phone = models.CharField(null=True, blank=True, max_length=20, default='+22507070707')
    bank_name = models.CharField(null=True, blank=True, default='Banque name', max_length=20, )
    account_number = models.IntegerField(null=True, blank=True, default='000000000000', )
    code_guichet = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    cle_rib = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    code_banque = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    iban = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    swift = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    bank_adress = models.CharField(null=True, blank=True, default='Plateau', max_length=20, )
    alternative_phone = models.CharField(null=True, blank=True, default='00000000', max_length=20, )
    nationalite = models.CharField(null=True, blank=True, default='00000000', max_length=70, )
    personal_mail = models.CharField(null=True, blank=True, default='email@sah.com', max_length=70)
    birthdate = models.DateField(null=True, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    salary = models.CharField(blank=True, max_length=100, null=True)
    dpt = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name="service", blank=True, null=True)
    job_title = models.CharField(null=True, blank=True, max_length=50, verbose_name="Titre du poste")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")
    photo = models.ImageField(null=True, blank=True, default='urap/users/5.png', upload_to='urap/users')
    sortie = models.SmallIntegerField(null=True, blank=True, default=0)
    is_deleted = models.SmallIntegerField(null=True, blank=True, default=0)
    slug = models.SlugField(null=True, blank=True, help_text="slug field", verbose_name="slug ", unique=True,
                            editable=False)
    created_at = models.DateTimeField(auto_now_add=now, )
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username}- {self.user.first_name} {self.user.last_name} ({self.dpt})"

    class Meta:
        permissions = (
            ("can_edit_employee", "Can edit employee"),
            ("can_create_employee", "Can create employee"),
            ("can_view_salary", "can view salary"),
        )


class Patient(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    code_patient = models.CharField(max_length=100, unique=True)
    code_vih = models.CharField(max_length=100, blank=True, unique=True)
    nom = models.CharField(max_length=225)
    prenoms = models.CharField(max_length=225)
    contact = models.CharField(max_length=225)
    situation_matrimoniale = models.CharField(max_length=225, choices=situation_matrimoniales_choices)
    lieu_naissance = models.CharField(max_length=200)
    date_naissance = models.DateField(null=True, blank=True)
    genre = models.CharField(max_length=10, choices=Sexe_choices)
    nationalite = models.CharField(max_length=200)
    ethnie = models.CharField(null=True, blank=True, max_length=100)
    profession = models.CharField(max_length=100, null=True, blank=True)
    nbr_enfants = models.PositiveIntegerField(default=0, null=True, blank=True)
    groupe_sanguin = models.CharField(choices=Goupe_sanguin_choices, max_length=20, null=True)
    niveau_etude = models.CharField(max_length=100, null=True, blank=True)
    employeur = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(null=True, blank=True)
    localite = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    cascontact = models.ManyToManyField('self')
    status = models.CharField(choices=Patient_statut_choices, max_length=100, default='Aucun', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        # permissions = (
        #     ('view_patient', 'Can view patient'),
        #     ('edit_patient', 'Can edit patient'),
        #     ('delete_patient', 'Can delete patient'),
        # )

    @property
    def services_passed(self):
        consultation_services = self.consultation_set.values('services')
        hospitalization_services = self.hospitalized.values('activite__service')
        all_service_ids = set(service['services'] for service in consultation_services).union(
            set(service['activite__service'] for service in hospitalization_services))
        all_services = Service.objects.filter(id__in=all_service_ids)
        return all_services

    def save(self, *args, **kwargs):
        if not self.code_vih:
            self.code_vih = get_incremental_code()
        if not self.code_patient:
            self.code_patient = self.get_incremental_code()
        if not self.avatar:
            name = f"{self.nom} {self.prenoms}"
            bg_color = (0, 122, 255) if self.genre == 'HOMME' else (0, 122, 255)
            avatar_image = generate_avatar(name, bg_color)
            self.avatar.save(f"{self.code_patient}.png", ContentFile(avatar_image.read()), save=False)
        super(Patient, self).save(*args, **kwargs)

    def generate_numeric_uuid(self):
        # Génère un UUID et convertit en une chaîne numérique de longueur 8
        return str(random.randint(10000000, 99999999))

    def get_incremental_code(self) -> str:
        current_year = datetime.date.today().year
        current_year_short = str(current_year)[2:]

        # Use a transaction to ensure atomicity and uniqueness
        with transaction.atomic():
            # Lock the table to prevent race conditions
            latest_patient = Patient.objects.select_for_update().filter(
                code_vih__startswith=current_year_short
            ).aggregate(Max('code_vih'))['code_vih__max']

            if latest_patient:
                # Extract the numeric part and increment it
                latest_number = int(latest_patient.split('-')[1])
                new_number = latest_number + 1
            else:
                # If no patient for the current year, start with 1
                new_number = 1

            # Format the new number with leading zeros
            random_digits = random.randint(100000, 999999)
            new_code = f"{current_year_short}-{random_digits}"

        return new_code

    # def get_incremental_code(self) -> str:
    #     current_year = datetime.date.today().year
    #     current_year_short = str(current_year)[2:]
    #
    #     # Use a transaction to ensure atomicity and uniqueness
    #     with transaction.atomic():
    #         # Lock the table to prevent race conditions
    #         latest_patient = Patient.objects.select_for_update().filter(code_vih__startswith=current_year_short
    #                                                                     ).aggregate(Max('code_vih'))['code_vih__max']
    #
    #         if latest_patient:
    #             # Extract the numeric part and increment it
    #             latest_number = int(latest_patient.split('-')[1])
    #             new_number = latest_number + 1
    #         else:
    #             # If no patient for the current year, start with 1
    #             new_number = 1
    #
    #         # Format the new number with leading zeros
    #         new_code = f"{current_year_short}-{new_number:06d}"
    #
    #     return new_code

    # Optionally, you can also use signals to handle the avatar generation
    # @receiver(post_save, sender=Patient)
    # def create_patient_avatar(sender, instance, created, **kwargs):
    #     if created and not instance.avatar:
    #         name = f"{instance.nom} {instance.prenoms}"
    #         avatar_image = generate_avatar(name)
    #         instance.avatar.save(f"{instance.code_patient}.png", ContentFile(avatar_image.read()), save=False)
    #         instance.save()

    @property
    def calculate_age(self):
        if self.date_naissance:
            today = datetime.date.today()
            age = today.year - self.date_naissance.year - (
                    (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
            return age
        else:
            return None

    @property
    def latest_constante(self):
        return self.constantes.order_by('-created_at').first()

    def __str__(self):
        # Ensure nom and prenoms are not None, using default values if necessary
        prenoms = self.prenoms if self.prenoms else "Inconnu"
        nom = self.nom if self.nom else "Inconnu"
        return f'{prenoms} {nom} '


class PatientUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Patient, on_delete=models.CASCADE)


class PatientGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Patient, on_delete=models.CASCADE)
