import streamlit as st
import json
import os
import random
from datetime import datetime
import matplotlib.pyplot as plt

save_file = "save.json"

quests = [
    {"name": "Run", "xp": 50},
    {"name": "Read book", "xp": 30},
    {"name": "Drink water", "xp": 20},
    {"name": "Eat 3k calories", "xp": 70}
]

# -------------------- SAVE/LOAD --------------------
def load_game():
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            return json.load(f)
    else:
        return {
            "xp": 0,
            "level": 0,
            "completed_today": [],
            "success": {}  # track {quest: {"success": X, "fail": Y}}
        }

def save_game(data):
    with open(save_file, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- ML PART --------------------
def thompson_sampling_suggestions(data, n=2):
    quest_scores = []
    for quest in quests:
        stats = data["success"].get(quest["name"], {"success": 1, "fail": 1})
        alpha = 1 + stats["success"]
        beta = 1 + stats["fail"]
        sampled_p = random.betavariate(alpha, beta)
        quest_scores.append((sampled_p, quest["name"]))

    quest_scores.sort(reverse=True)
    return [q for _, q in quest_scores[:n]]

# -------------------- GAME LOGIC --------------------
def completed_quest(data, quest_name):
    if quest_name in data["completed_today"]:
        st.warning(f"You already completed '{quest_name}' today!")
        return

    selected = next(q for q in quests if q["name"] == quest_name)
    data["completed_today"].append(selected["name"])

    # Update success stats
    stats = data["success"].get(selected["name"], {"success": 1, "fail": 1})
    stats["success"] += 1
    data["success"][selected["name"]] = stats

    # Adaptive XP
    total = stats["success"] + stats["fail"]
    success_rate = stats["success"] / total if total > 0 else 1.0
    bonus = 1.0 + (0.5 * (1 - success_rate))  # harder quests give more XP
    gained_xp = int(selected["xp"] * bonus)

    data["xp"] += gained_xp
    st.success(f"✅ Completed: {quest_name} (+{gained_xp} XP)")
    check_level_up(data)

def record_skip(data, quest_name):
    stats = data["success"].get(quest_name, {"success": 1, "fail": 1})
    stats["fail"] += 1
    data["success"][quest_name] = stats
    st.info(f"❌ You skipped {quest_name}")

def check_level_up(data):
    new_level = data["xp"] // 100
    if new_level > data["level"]:
        data["level"] = new_level
        st.balloons()
        st.success(f"🎉 LEVEL UP! You are now level {data['level']}")

# -------------------- VISUALIZATION --------------------
def plot_success_probabilities(data):
    names = []
    probs = []
    for quest in quests:
        stats = data["success"].get(quest["name"], {"success": 1, "fail": 1})
        alpha = 1 + stats["success"]
        beta = 1 + stats["fail"]
        mean_prob = alpha / (alpha + beta)
        names.append(quest["name"])
        probs.append(mean_prob)

    fig, ax = plt.subplots()
    ax.bar(names, probs, color="skyblue")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Estimated Success Probability")
    ax.set_title("Quest Success Predictions (ML)")
    return fig

# -------------------- STREAMLIT APP --------------------
def main():
    st.title("🎮 Life Quest RPG with AI")
    data = load_game()

    st.sidebar.header("Player Stats")
    st.sidebar.write(f"**XP:** {data['xp']}")
    st.sidebar.write(f"**Level:** {data['level']}")

    st.header("📋 Today's Quests")
    for quest in quests:
        if quest["name"] in data["completed_today"]:
            st.write(f"✅ {quest['name']} (done)")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Complete {quest['name']}", key=f"c_{quest['name']}"):
                    completed_quest(data, quest["name"])
                    save_game(data)
            with col2:
                if st.button(f"Skip {quest['name']}", key=f"s_{quest['name']}"):
                    record_skip(data, quest["name"])
                    save_game(data)

    st.header("🤖 AI Suggested Quests")
    suggestions = thompson_sampling_suggestions(data)
    st.write("Based on your past performance, try:")
    for s in suggestions:
        st.write(f"👉 {s}")

    st.header("📊 Progress Tracker")
    fig = plot_success_probabilities(data)
    st.pyplot(fig)

    if st.button("💾 Save Progress"):
        save_game(data)
        st.success("Game saved!")

if __name__ == "__main__":
    main()
