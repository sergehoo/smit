import datetime
import io
import json
import random
import uuid
from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import Max
from django.utils.timezone import now
from django_countries.fields import CountryField
from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
import qrcode

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
    ('Fille de Menage', 'Fille de Menage'),
    ('Employer de maison', 'Employer de maison'),
    ('Commercant', 'Commercant'),
    ('Cultuvateur', 'Cultuvateur'),
    ('Planteur', 'Planteur'),
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

type_localite_choices = [
    ('Commune', 'Commune'),
    ('Village', 'Village'),
    ('Ville', 'Ville'),
    ('Quartier', 'Quartier'),
]

communes_et_quartiers_choices = [
    ('Abobo', 'Abobo'),
    ('Adjamé', 'Adjamé'),
    ('Aboisso', 'Aboisso'),
    ('Abengourou', 'Abengourou'),
    ('Adzopé', 'Adzopé'),

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
    ('Treichville', 'Treichville'),
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
    from pharmacy.models import Pharmacy
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee", )
    qlook_id = models.CharField(default=qlook, unique=True, editable=False, max_length=100)
    gender = models.CharField(choices=Sexe_choices, max_length=100, null=True, blank=True, )
    situation_matrimoniale = models.CharField(choices=situation_matrimoniales_choices, max_length=100, null=True,
                                              blank=True, )
    phone = models.CharField(null=True, blank=True, max_length=20, default='+22507070707')
    nationalite = models.CharField(null=True, blank=True, default='00000000', max_length=70, )
    email = models.CharField(null=True, blank=True, default='email@sah.com', max_length=70)
    birthdate = models.DateField(null=True, blank=True)
    departement = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name="service", blank=True, null=True)
    pharmacie = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, verbose_name="Pharmacie", blank=True, null=True)
    photo = models.ImageField(null=True, blank=True, default='urap/users/5.png', upload_to='urap/users')
    sortie = models.SmallIntegerField(null=True, blank=True, default=0)
    is_deleted = models.SmallIntegerField(null=True, blank=True, default=0)
    slug = models.SlugField(null=True, blank=True, help_text="slug field", verbose_name="slug ", unique=True,
                            editable=False)
    created_at = models.DateTimeField(auto_now_add=now, )
    history = HistoricalRecords()

    def __str__(self):
        return f" {self.user.first_name} {self.user.last_name} | {self.departement}"

    class Meta:
        permissions = (
            ("can_edit_employee", "Can edit employee"),
            ("can_create_employee", "Can create employee"),
            ("can_view_salary", "can view salary"),
            ("can_view_employee", "can view employee"),
        )


class PolesRegionaux(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name if self.name else "Unnamed Pole"


class HealthRegion(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    poles = models.ForeignKey(PolesRegionaux, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Region"


class DistrictSanitaire(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True, )
    region = models.ForeignKey(HealthRegion, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(null=True, blank=True, )
    geojson = models.JSONField(null=True, blank=True, )
    previous_rank = models.IntegerField(null=True, blank=True)

    def clean(self):
        # Valider le champ `geojson` si présent
        if self.geojson:
            try:
                json.dumps(self.geojson)  # Vérifie que le contenu est JSON
            except ValueError:
                raise ValidationError("Le champ GeoJSON n'est pas valide.")

    def __str__(self):
        return f'{self.nom}---->{self.region}'

    def __str__(self):
        return f'{self.nom}---->{self.region}'


class Location(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    type = models.CharField(choices=type_localite_choices, max_length=100, null=True, blank=True)
    population = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )

    def __str__(self):
        return f"{self.name} - {self.district}"


class Patient(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    code_patient = models.CharField(max_length=100, unique=True)
    code_vih = models.CharField(max_length=100, blank=True, unique=True)
    nom = models.CharField(max_length=225)
    prenoms = models.CharField(max_length=225)
    contact = models.CharField(max_length=225)
    adresse_mail = models.CharField(max_length=50, blank=True, unique=True)
    situation_matrimoniale = models.CharField(max_length=225, choices=situation_matrimoniales_choices)
    lieu_naissance = models.CharField(max_length=200, )
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
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    localite = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(choices=Patient_statut_choices, max_length=100, default='Aucun', null=True, blank=True)
    urgence = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        permissions = (
            ('view_patient_name', 'Can view patient name'),
            ('view_dossier_patient', 'Can View dossier patient'),
            # ('delete_patient', 'Can delete patient'),
        )

    def generate_qr_code(self):
        """
        Génère un QR code pour le patient contenant des informations pertinentes.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Construire les données du QR code
        qr_data = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"N:{self.nom};{self.prenoms}\n"
            f"TEL:{self.contact}\n"
            f"EMAIL:{self.adresse_mail or 'non spécifié'}\n"
            f"ORG:SMIT-KENEYA\n"
            f"TITLE:Patient\n"
            f"NOTE:Code Patient: {self.code_patient}\n"
            "END:VCARD"
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Générer l'image du QR code
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"qr_code_{self.code_patient}.png"

        self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)

    @property
    def latest_poids(self):
        # Récupérer le poids le plus récent à partir des constantes ou des suivis
        constante = self.constantes.order_by('-created_at').first()
        return constante.poids if constante and constante.poids else None

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
        if not self.qr_code:
            self.generate_qr_code()
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


class PatientAdresses(models.Model):
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    current = models.BooleanField(default=False)
    staydate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.location} - {self.current} ({self.staydate})"


class PatientUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Patient, on_delete=models.CASCADE)


class PatientGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Patient, on_delete=models.CASCADE)


class CasContact(models.Model):
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='case_contacts',
        verbose_name=_("Patient")
    )
    contact_person = models.CharField(
        max_length=255,
        verbose_name=_("Contact Person Name"))

    phone_number = models.CharField(
        max_length=15,
        verbose_name=_("Phone Number"),
        help_text="Enter a valid phone number with country code, e.g., +1234567890"
    )

    relationship = models.CharField(
        max_length=255,
        choices=[
            ('FAMILY', _('Family Member')),
            ('FRIEND', _('Friend')),
            ('COWORKER', _('Coworker')),
            ('NEIGHBOR', _('Neighbor')),
            ('OTHER', _('Other')),
        ],
        verbose_name=_("Relationship to Patient")
    )
    contact_frequency = models.CharField(
        max_length=255,
        choices=[
            ('DAILY', _('Daily')),
            ('WEEKLY', _('Weekly')),
            ('OCCASIONAL', _('Occasional')),
        ],
        verbose_name=_("Frequency of Contact")
    )
    date_contact = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Last Contact")
    )
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Location of Interaction")
    )
    prevention_measures = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Prevention Measures Taken")
    )
    details = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Details")
    )
    smsdepistage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Case Contact")
        verbose_name_plural = _("Case Contacts")
        unique_together = ('patient', 'contact_person')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} - {self.contact_person}"

    def clean(self):
        if not self.phone_number.startswith('+'):
            raise ValidationError({
                'phone_number': _("Phone number must include the country code and start with '+'.")
            })

    # def send_sms(self, message):
    #     """Send an SMS to the contact using Twilio."""
    #     try:
    #         # Replace with your Twilio credentials
    #         TWILIO_ACCOUNT_SID = 'your_account_sid'
    #         TWILIO_AUTH_TOKEN = 'your_auth_token'
    #         TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'
    #
    #         client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    #
    #         message = client.messages.create(
    #             body=message,
    #             from_=TWILIO_PHONE_NUMBER,
    #             to=self.phone_number
    #         )
    #
    #         return message.sid
    #     except Exception as e:
    #         raise ValidationError({
    #             'phone_number': _(f"Failed to send SMS: {e}")
    #         })


class Maladie(models.Model):
    CATEGORY_CHOICES = [
        ('infectieuse', 'Maladies infectieuses'),
        ('cardiovasculaire', 'Maladies cardiovasculaires'),
        ('respiratoire', 'Maladies respiratoires'),
        ('metabolique', 'Maladies métaboliques'),
        ('neurologique', 'Maladies neurologiques'),
        ('autoimmune', 'Maladies auto-immunes'),
        ('cancer', 'Cancers'),
        ('genetique', 'Maladies génétiques'),
        ('psychiatrique', 'Maladies psychiatriques'),
        ('musculosquelettique', 'Maladies musculosquelettiques'),
        ('dermatologique', 'Maladies dermatologiques'),
        ('gastrointestinale', 'Maladies gastro-intestinales'),
        ('urologique', 'Maladies urologiques et rénales'),
        ('rare', 'Maladies rares'),
        ('mode_de_vie', 'Maladies liées au mode de vie'),
        ('autre', 'Autres'),
    ]

    SEVERITY_CHOICES = [
        ('leger', 'Léger'),
        ('modere', 'Modéré'),
        ('grave', 'Grave'),
    ]

    nom = models.CharField(max_length=255)  # Nom de la maladie
    categorie = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='autre'
    )  # Catégorie de la maladie
    description = models.TextField(blank=True, null=True)  # Description de la maladie
    gravite = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='leger'
    )  # Gravité de la maladie
    date_diagnostic = models.DateField(blank=True, null=True)  # Date du diagnostic
    medecin_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maladies_traitees'
    )  # Médecin ayant diagnostiqué la maladie
    patient = models.ForeignKey(
        'Patient',  # Association avec un patient (si applicable)
        on_delete=models.CASCADE,
        related_name='maladies',
        null=True,
        blank=True
    )
    traitements = models.TextField(blank=True, null=True)  # Détails des traitements proposés
    observations = models.TextField(blank=True, null=True)  # Observations ou remarques supplémentaires

    date_enregistrement = models.DateTimeField(auto_now_add=True)  # Date d'ajout dans le système
    date_mise_a_jour = models.DateTimeField(auto_now=True)  # Dernière mise à jour

    def __str__(self):
        return f"{self.nom}"

    class Meta:
        verbose_name = "Maladie"
        verbose_name_plural = "Maladies"
        ordering = ['categorie', 'nom']
