
// ===== DONNÉES (chargées depuis la base de données via Flask) =====
// Le bloc "const zones = {...}" codé en dur est remplacé par un appel API.
// Toutes les fonctions calculer(), afficher(), animer(), reset() sont
// conservées à l'identique — seule la source des données change.

let zones = {};  // sera rempli par fetch('/api/zones') au chargement

fetch('/api/zones')
    .then(function(response) { return response.json(); })
    .then(function(data)     { zones = data; })
    .catch(function() {
        // Secours si le serveur Flask est inaccessible
        zones = {
            adjame:   { nom: "Adjamé",    base: 62, nuit: 78, jour: 48, conseil: "Évitez le grand marché et la gare routière la nuit. Ne montrez jamais votre téléphone. Gardez votre sac devant vous." },
            cocody:   { nom: "Cocody",    base: 22, nuit: 35, jour: 12, conseil: "Cocody reste le plus sûr. Attention aux zones périphériques (Angré, Danga) la nuit. Évitez d'afficher des signes de richesse." },
            yopougon: { nom: "Yopougon",  base: 55, nuit: 72, jour: 32, conseil: "Évitez les raccourcis sombres la nuit. Privilégiez les axes éclairés. Verrouillez vos portières en voiture." },
            abobo:    { nom: "Abobo",     base: 70, nuit: 85, jour: 45, conseil: "Zone à haut risque. Ne marchez jamais seul(e) la nuit. Évitez la gare routière et derrrière rail et Pk 18 après 20h. Prenez un taxi fiable un yango et partager votre position à une connaissance." }
        };
    });

// ===== CALCUL =====
function calculer(e) {
    e.preventDefault();

    const age     = parseInt(document.getElementById('age').value);
    const sexe    = document.getElementById('sexe').value;
    const zoneId  = document.getElementById('zone').value;

    if(!age || !sexe || !zoneId) return false;

    const z = zones[zoneId];
    let risque = z.base;

    // Ajustement âge
    if      (age < 15)  risque -= 15;
    else if (age <= 25) risque += 10;
    else if (age <= 35) risque += 5;
    else if (age <= 50) risque += 0;
    else if (age <= 65) risque += 8;
    else                risque += 12;

    // Ajustement sexe
    risque += (sexe === 'homme') ? 3 : 5;

    // Bornes
    risque = Math.max(5, Math.min(95, Math.round(risque)));

    const nuit = Math.min(95, z.nuit + (risque - z.base));
    const jour = Math.max(5, Math.round(z.jour + (risque - z.base) * 0.5));

    afficher(risque, nuit, jour, age, sexe, z);
    return false;
}

// ===== AFFICHAGE =====
function afficher(pct, nuit, jour, age, sexe, z) {

    document.getElementById('resultat').style.display = 'block';

    // Couleur
    let couleur;
    if      (pct <= 25) couleur = '#00c853';
    else if (pct <= 50) couleur = '#f9a825';
    else if (pct <= 70) couleur = '#ff9800';
    else                couleur = '#ff4757';

    // Jauge
    const circ   = 2 * Math.PI * 60;  // 377
    const offset = circ - (pct / 100) * circ;
    const barre  = document.getElementById('barre');

    barre.style.strokeDashoffset = circ;
    setTimeout(() => {
        barre.style.stroke = couleur;
        barre.style.strokeDashoffset = offset;
    }, 50);

    // Animation chiffre
    animer('pct', 0, pct, 1500, couleur);

    // Niveau
    const niv = document.getElementById('niveau');
    if      (pct <= 25) { niv.textContent = '🟢 Faible';       niv.className = 'niveau vert';   }
    else if (pct <= 50) { niv.textContent = '🟡 Modéré';       niv.className = 'niveau jaune';  }
    else if (pct <= 70) { niv.textContent = '🟠 Élevé';        niv.className = 'niveau orange'; }
    else                { niv.textContent = '🔴 Très élevé';   niv.className = 'niveau rouge';  }

    // Infos
    document.getElementById('rZone').textContent = z.nom;
    document.getElementById('rAge').textContent  = age + ' ans';
    document.getElementById('rSexe').textContent = sexe === 'homme' ? 'Homme' : 'Femme';

    const rN = document.getElementById('rNuit');
    rN.textContent = nuit + '%';
    rN.style.color = nuit > 60 ? '#ff4757' : nuit > 40 ? '#ff9800' : '#00c853';

    const rJ = document.getElementById('rJour');
    rJ.textContent = jour + '%';
    rJ.style.color = jour > 60 ? '#ff4757' : jour > 40 ? '#ff9800' : '#00c853';

    // Conseil
    document.getElementById('conseil').textContent = '💡 ' + z.conseil;

    // Scroll
    document.getElementById('resultat').scrollIntoView({ behavior:'smooth', block:'center' });
}

// ===== ANIMATION =====
function animer(id, de, a, duree, couleur) {
    const el = document.getElementById(id);
    const debut = performance.now();

    function step(now) {
        const p = Math.min((now - debut) / duree, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(de + (a - de) * ease) + '%';
        el.style.color = couleur;
        if (p < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}

// ===== RESET =====
function reset() {
    document.getElementById('resultat').style.display = 'none';
    document.getElementById('barre').style.strokeDashoffset = 377;
    document.getElementById('pct').textContent = '0%';
    document.getElementById('formulaire').reset();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
