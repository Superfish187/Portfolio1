// Lab-only adapters: these registry components need string children, which Astro slots can't pass.
import DecryptedText from "./DecryptedText";
import { TextEffect } from "./TextEffect";

const heading = "display text-2xl";

export const Decrypted = ({ text }: { text: string }) => (
  <h3 className={heading}>
    <DecryptedText text={text} animateOn="view" sequential revealDirection="start" speed={40} />
  </h3>
);

export const Effect = ({ text }: { text: string }) => (
  <TextEffect as="h3" per="char" preset="fade-in-blur" className={heading}>
    {text}
  </TextEffect>
);
