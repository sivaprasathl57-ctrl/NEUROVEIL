function showTip(type) {
  const tips = {
    phishing: "Phishing is a fake message or email that tries to steal your data. Always check the sender and avoid unknown links.",
    otp: "Never share your OTP with anyone. Real banks or companies will never ask for it.",
    calls: "If someone calls and asks for personal details, verify the number before responding.",
    upi: "Always read the payment request carefully. Do not approve unknown UPI requests."
  };

  alert(tips[type]);
}

function answerQuiz(isCorrect) {
  const result = document.getElementById("result");
  if (isCorrect) {
    result.textContent = "Correct! Never share your OTP with anyone.";
    result.style.color = "#4dff88";
  } else {
    result.textContent = "Wrong answer. OTP should always be kept secret.";
    result.style.color = "#ff5c5c";
  }
}