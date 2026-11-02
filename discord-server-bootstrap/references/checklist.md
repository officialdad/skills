# Verification checklist

Run each item. Report any item you cannot run as unconfirmed.

## Before the build

- [ ] The spec passes `bootstrap.sh --check-spec`.
- [ ] The bot has Administrator and sits above the roles it manages.
- [ ] The server has the Community feature on. Onboarding and rules screening need it.
- [ ] `.env` has mode 600.

## After the build

- [ ] Run `bootstrap.sh` a second time. It creates nothing new.
- [ ] List channels. Each name and category matches the spec.
- [ ] Open the server as a member with no roles. Only the intended channels show.
- [ ] Read each pin. No marker text, no `{{...}}` placeholder.
- [ ] Count invites. One permanent invite remains when the spec has `invite_channel`. No new invite exists when it does not.
- [ ] Open the invite in a private window with a fresh account. The rules screen shows, then the welcome channel.
- [ ] Check onboarding default channels.
- [ ] For each forum, read back its posts through the API. Titles match the spec and the pinned post is pinned.
- [ ] Open each forum as a member. The post list, the layout, and posting a reply all work. A bot cannot test this, so a human must.
- [ ] Check no forum post notified anyone.

## Help bot

- [ ] Ask an on-topic question in the help channel. The answer comes from the knowledge file.
- [ ] Ask an off-topic question. The bot gives the off-topic reply.
- [ ] Ask an unknown question. The bot pings the organizer role.
- [ ] Post a fake key. The bot deletes it.
- [ ] Run `/getkey` as a member. The key arrives, the role grants, a second run says it is claimed.
- [ ] Form a team with the button. The private room exists and only members see it.
- [ ] Restart with `--force-recreate`. The team button still works.
