const express = require("express");
const cors = require("cors");
const admin = require("firebase-admin");

admin.initializeApp({
  credential: admin.credential.applicationDefault()
});

const db = admin.firestore();
const app = express();

app.use(cors());
app.use(express.json());

app.post("/disposeWaste", async (req, res) => {
  const { userId, wasteType, disposalStatus, credits } = req.body;

  try {
    // 1️⃣ Waste Separation Dashboard data
    await db.collection("waste_logs").add({
      wasteType,
      disposalStatus,
      timestamp: new Date()
    });

    // 2️⃣ Wallet Transaction Dashboard data
    await db.collection("transactions").add({
      userId,
      credits,
      reason: `${wasteType} disposal`,
      timestamp: new Date()
    });

    // 3️⃣ Update Wallet
    const userRef = db.collection("users").doc(userId);
    await db.runTransaction(async (t) => {
      const doc = await t.get(userRef);
      const current = doc.exists ? doc.data().totalCredits : 0;
      t.set(userRef, { totalCredits: current + credits }, { merge: true });
    });

    res.json({ status: "success" });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.listen(5000, () => {
  console.log("Backend running on port 5000");
});