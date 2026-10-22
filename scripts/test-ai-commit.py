import http.server, json, os, re, subprocess, sys, tempfile, threading, shutil

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-commit.py")
PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ok   {name}")
    else: FAIL += 1; print(f"  FAIL {name}  {detail}")

# ---------- fake Ollama ----------
class State: mode="good"; prompts=[]; calls=0; bodies=[]
GOOD = "feat(niri): add screenshot binds and tune the layout\n\n- bind Print to screenshot\n- reduce gaps"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_POST(self):
        n=int(self.headers["Content-Length"]); body=json.loads(self.rfile.read(n))
        State.calls+=1; State.prompts.append(body["messages"][1]["content"]); State.bodies.append(body)
        m=State.mode
        if m=="404": self.send_response(404); self.end_headers(); return
        if m=="good": out=GOOD
        elif m=="think": out="<think>hmm let me see</think>\n```\n"+GOOD+"\n```"
        elif m=="garbage": out="Sure! Here is a commit message for you."
        elif m=="long_then_good": out = ("feat(niri): "+"x"*80) if State.calls%2==1 else GOOD
        else: out=GOOD
        data=json.dumps({"message":{"content":out}}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(data)
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),H); PORT=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()

def sh(cmd, cwd, env=None, check_=True):
    e=dict(os.environ); e.update(env or {})
    return subprocess.run(cmd,cwd=cwd,shell=isinstance(cmd,str),capture_output=True,text=True,env=e)

def run(repo, *args, mode=None, url=None, extra=None):
    if mode: State.mode=mode
    env={"ROUDIX_AI_URL": url or f"http://127.0.0.1:{PORT}", "GIT_EDITOR":"true", "ROUDIX_AI_TIMEOUT":"5"}
    env.update(extra or {})
    return sh(["python3",SCRIPT,*args],repo,env)

def mkrepo(autos=3, with_secret=True, lock_only=False, nonauto_before=False):
    d=tempfile.mkdtemp(prefix="rx-")
    g=lambda c: sh(c,d)
    g("git init -q -b dev . && git config user.email t@t && git config user.name t")
    os.makedirs(f"{d}/modules/home/desktop/niri",exist_ok=True)
    open(f"{d}/modules/home/desktop/niri/_binds.nix","w").write("{ }\n")
    open(f"{d}/flake.lock","w").write('{"nodes":{}}\n')
    g("git add -A && git commit -qm base")
    if nonauto_before:
        open(f"{d}/NOTE","w").write("x\n"); g("git add -A && git commit -qm 'fix: a real commit'")
    for i in range(autos):
        if lock_only:
            open(f"{d}/flake.lock","a").write(f'{{"narHash":"sha256-LOCKCONTENT{i}"}}\n')
        else:
            p=f"{d}/modules/home/desktop/niri/_binds.nix"
            extra=""
            if with_secret and i==1:
                extra='  token = "ghp_abcdefghijklmnopqrstuvwxyz0123456789";\n  password = "hunter2";\n'
            open(p,"a").write(f'  bind{i} = "Print";\n{extra}')
            if i==2: open(f"{d}/flake.lock","a").write('{"narHash":"sha256-LOCKCONTENT"}\n')
        g(f"git add -A && git commit -qm 'auto: 1 file changed, {i+1} insertion(+)'")
    return d
log=lambda d: sh("git log --format=%s",d).stdout.strip().splitlines()
tree=lambda d: sh("git rev-parse HEAD^{tree}",d).stdout.strip()

print("1. dry-run: affiche le message, ne change rien")
d=mkrepo(); State.calls=0; State.prompts=[]; before=log(d)
r=run(d,"squash","--dry-run",mode="good")
check("rc 0", r.returncode==0, r.stderr)
check("message IA affiché", "feat(niri): add screenshot binds" in r.stdout, r.stdout)
check("historique inchangé", log(d)==before)
p=State.prompts[0]
check("secrets absents du prompt", "ghp_abcdef" not in p and "hunter2" not in p)
check("valeurs masquées", "<redacted>" in p)
check("flake.lock résumé, contenu non envoyé", "LOCKCONTENT" not in p and "[summarised" in p)
check("scope suggéré = niri", "Suggested scope: niri" in p, p[:80])

print("2. squash --yes: 3 auto -> 1, arbre identique, sauvegarde, undo")
d=mkrepo(); t0=tree(d)
r=run(d,"squash","--yes",mode="good")
L=log(d)
check("rc 0", r.returncode==0, r.stderr)
check("historique = base + 1 commit", len(L)==2 and L[0].startswith("feat(niri): add screenshot binds"), L)
check("arbre identique", tree(d)==t0)
check("ref de sauvegarde", sh("git rev-parse --verify -q refs/roudix/pre-squash",d).returncode==0)
sh("git reset --soft refs/roudix/pre-squash",d)
check("undo restaure 4 commits", len(log(d))==4 and tree(d)==t0)

print("3. nettoyage de la sortie du modèle (<think>, ```)")
d=mkrepo(); r=run(d,"squash","--dry-run",mode="think")
check("<think> et fences retirés", r.stdout.startswith("feat(niri):") and "think" not in r.stdout and "```" not in r.stdout, r.stdout)

print("4. réponse invalide x2 -> repli déterministe")
d=mkrepo(); State.calls=0; r=run(d,"squash","--dry-run",mode="garbage")
check("rc 0", r.returncode==0, r.stderr)
check("2 tentatives", State.calls==2, State.calls)
check("repli valide", re.match(r"^chore\(\w+\): update \d+ files|^chore\(\w+\): update \w+",r.stdout) is not None, r.stdout)
check("annonce 'fallback'", "fallback" in r.stderr)

print("5. 1er essai trop long, 2e bon -> retry utilisé")
d=mkrepo(); State.calls=0; r=run(d,"squash","--dry-run",mode="long_then_good")
check("message final = bon", "feat(niri): add screenshot binds" in r.stdout and State.calls==2, (State.calls,r.stdout))

print("6. serveur éteint -> repli, pas de blocage")
d=mkrepo(); r=run(d,"squash","--dry-run",url="http://127.0.0.1:9")
check("rc 0 et repli", r.returncode==0 and "chore(" in r.stdout, (r.returncode,r.stdout,r.stderr))
check("dit pourquoi", "unreachable" in r.stderr)

print("7. modèle absent (404) -> indice ollama pull")
d=mkrepo(); r=run(d,"squash","--dry-run",mode="404")
check("hint pull", "ollama pull" in r.stderr, r.stderr); check("repli", "chore(" in r.stdout)

print("8. commits déjà poussés: jamais réécrits, seuls les nouveaux (locaux) sont regroupés")
def push_remote(d):
    bare=tempfile.mkdtemp(prefix="bare-"); sh(f"git init -q --bare {bare}",d)
    sh(f"git remote add origin {bare} && git push -q origin dev",d)
def add_autos(d, n):
    for i in range(n):
        open(f"{d}/modules/home/desktop/niri/_binds.nix","a").write(f'  local{i} = "x";\n')
        sh(f"git add -A && git commit -qm 'auto: 1 file changed, local {i}'",d)
# 8a. tout est poussé, rien de nouveau
d=mkrepo(); push_remote(d); before=log(d)
r=run(d,"squash","--yes",mode="good")
check("8a rien à regrouper, historique intact", r.returncode==0 and log(d)==before and "no unpushed" in r.stderr, r.stderr)
# 8b. ta situation: 3 anciens poussés + 2 nouveaux locaux
d=mkrepo(); push_remote(d); add_autos(d,2); pushed=sh("git rev-parse origin/dev",d).stdout.strip()
State.prompts=[]; r=run(d,"squash","--yes",mode="good"); L=log(d)
check("8b seuls les 2 nouveaux regroupés (base + 3 poussés + 1)", r.returncode==0 and len(L)==5 and L[0].startswith("feat(niri)") and sum(1 for x in L if x.startswith("auto:"))==3, L)
check("8b l'historique poussé est un ancêtre: push normal, sans force", sh(f"git merge-base --is-ancestor {pushed} HEAD",d).returncode==0)
# 8c. --allow-pushed regroupe tout, et prévient
d=mkrepo(); push_remote(d); add_autos(d,2)
r=run(d,"squash","--yes","--allow-pushed",mode="good")
check("8c --allow-pushed regroupe les 5 et avertit du force-push", r.returncode==0 and len(log(d))==2 and "force-with-lease" in r.stderr, (r.returncode,r.stderr,log(d)))
# 8d. dry-run montre le message pour les nouveaux seulement
d=mkrepo(); push_remote(d); add_autos(d,2); before=log(d); State.prompts=[]
r=run(d,"squash","--dry-run",mode="good")
check("8d dry-run: message affiché, 2 commits seulement, rien modifié", r.returncode==0 and "2 commit(s) -> 1" in r.stderr and log(d)==before, r.stderr)

print("9. arbre sale -> refus, rien ne bouge")
d=mkrepo(); open(f"{d}/modules/home/desktop/niri/_binds.nix","a").write("# dirty\n"); before=log(d)
r=run(d,"squash","--yes",mode="good")
check("refus + intact + backup non créé", r.returncode!=0 and log(d)==before and "uncommitted" in r.stderr, r.stderr)

print("10. HEAD n'est pas un commit auto -> rien à faire")
d=mkrepo(autos=0); r=run(d,"squash","--yes",mode="good")
check("rc 0 + message clair", r.returncode==0 and "no unpushed" in r.stderr, r.stderr)

print("11. un vrai commit avant les auto est préservé")
d=mkrepo(autos=2,nonauto_before=True); r=run(d,"squash","--yes",mode="good"); L=log(d)
check("base, 'fix: a real commit', 1 squash", len(L)==3 and L[1]=="fix: a real commit", L)

print("12. éditeur vidé -> commit annulé, historique restauré")
d=mkrepo(); t0=tree(d); before=log(d)
r=run(d,"squash",mode="good",extra={"GIT_EDITOR":"truncate -s 0"})
check("restauré", r.returncode!=0 and log(d)==before and tree(d)==t0, (r.returncode,r.stderr,log(d)))

print("13. seul flake.lock modifié -> message par règle, aucun appel au modèle")
d=mkrepo(lock_only=True); State.calls=0; r=run(d,"squash","--dry-run",mode="good")
check("règle deps, 0 appel", "chore(deps): update flake.lock" in r.stdout and State.calls==0, (State.calls,r.stdout))

print("14. message / commit sur le staged")
d=mkrepo(autos=0); r=run(d,"message",mode="good"); check("rien de stagé -> erreur", r.returncode!=0 and "nothing is staged" in r.stderr)
open(f"{d}/modules/home/desktop/niri/_binds.nix","a").write("  x = 1;\n"); sh("git add -A",d)
r=run(d,"message",mode="good"); check("message imprimé", r.returncode==0 and r.stdout.startswith("feat(niri)"), r.stdout)
r=run(d,"commit","--yes",mode="good"); check("commit créé", r.returncode==0 and log(d)[0].startswith("feat(niri)"), r.stderr)

print("15. ROUDIX_AI_CMD (ex: claude -p) au lieu d'Ollama")
d=mkrepo(); State.calls=0
r=run(d,"squash","--dry-run",extra={"ROUDIX_AI_CMD":"sh -c 'cat >/dev/null; echo \"fix(niri): handle a thing\"'"})
check("utilise la commande, pas Ollama", "fix(niri): handle a thing" in r.stdout and State.calls==0, (State.calls,r.stdout,r.stderr))

print("16. --offline + chemins avec espaces/accents")
d=mkrepo(autos=0); os.makedirs(f"{d}/dotfiles",exist_ok=True)
open(f"{d}/dotfiles/mon fichier é.txt","w").write("a\n"); sh("git add -A && git commit -qm 'auto: x'",d)
State.calls=0; r=run(d,"squash","--dry-run","--offline")
check("pas d'appel, nom lisible", State.calls==0 and "mon fichier é.txt" in r.stdout+r.stderr or "update mon fichier" in r.stdout, r.stdout)

print("17. VRAM: le modèle est déchargé tout de suite par défaut (keep_alive = 0)")
d=mkrepo(); State.bodies=[]; r=run(d,"squash","--dry-run",mode="good")
check("requête avec keep_alive == 0", State.bodies and State.bodies[0].get("keep_alive")==0, State.bodies[:1])
check("0 est un entier (pas la chaîne '0')", isinstance(State.bodies[0].get("keep_alive"), int))
d=mkrepo(); State.bodies=[]; r=run(d,"squash","--dry-run",mode="good",extra={"ROUDIX_AI_KEEP_ALIVE":"5m"})
check("ROUDIX_AI_KEEP_ALIVE=5m -> '5m'", State.bodies and State.bodies[0].get("keep_alive")=="5m", State.bodies[:1])
d=mkrepo(); State.bodies=[]; r=run(d,"squash","--dry-run",mode="good",extra={"ROUDIX_AI_KEEP_ALIVE":"300"})
check("ROUDIX_AI_KEEP_ALIVE=300 -> 300 (entier)", State.bodies and State.bodies[0].get("keep_alive")==300, State.bodies[:1])

print(f"\n{PASS} ok, {FAIL} échecs"); sys.exit(1 if FAIL else 0)
