"use client";

import { useEffect, useState } from "react";

const noticeKey = "taxsphere_flash_notice";

export function FlashNotice() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    const nextMessage = sessionStorage.getItem(noticeKey);
    if (!nextMessage) return;

    sessionStorage.removeItem(noticeKey);
    setMessage(nextMessage);
    const timeout = window.setTimeout(() => setMessage(""), 3500);
    return () => window.clearTimeout(timeout);
  }, []);

  if (!message) return null;

  return <div className="success-toast" role="status" aria-live="polite">{message}</div>;
}

export function queueFlashNotice(message: string) {
  sessionStorage.setItem(noticeKey, message);
}
