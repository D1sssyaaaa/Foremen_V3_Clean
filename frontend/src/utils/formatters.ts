/**
 * Форматирует номер телефона в формат +7 (XXX) XXX XX XX
 * @param phone - номер телефона (может быть в любом формате)
 * @returns отформатированный номер телефона
 */
export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return '';
  
  // Убираем все символы кроме цифр
  const digits = phone.replace(/\D/g, '');
  
  // Если номер начинается с 8, заменяем на 7
  const normalizedDigits = digits.startsWith('8') ? '7' + digits.slice(1) : digits;
  
  // Форматируем в +7 (XXX) XXX XX XX
  if (normalizedDigits.length >= 11) {
    const country = normalizedDigits.slice(0, 1);
    const code = normalizedDigits.slice(1, 4);
    const part1 = normalizedDigits.slice(4, 7);
    const part2 = normalizedDigits.slice(7, 9);
    const part3 = normalizedDigits.slice(9, 11);
    
    return `+${country} (${code}) ${part1} ${part2} ${part3}`;
  }
  
  // Если номер короче, возвращаем как есть
  return phone;
}
