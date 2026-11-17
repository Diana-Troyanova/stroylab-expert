document.documentElement.classList.add('js');
const byId = id => document.getElementById(id);
const menu = document.querySelector('.menu');
const nav = byId('site-nav');

function setMenu(open) {
  nav.classList.toggle('open', open);
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
}

menu.addEventListener('click', () => setMenu(!nav.classList.contains('open')));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && nav.classList.contains('open')) {
    setMenu(false);
    menu.focus();
  }
});

function value(id) {
  const field = byId(id);
  return field.type === 'number' ? field.valueAsNumber : Number(field.value);
}

function format(number, digits = 3) {
  const small = number !== 0 && Math.abs(number) < 10 ** -digits;
  return new Intl.NumberFormat('ru-RU', small
    ? { maximumSignificantDigits: 3, notation: 'scientific' }
    : { maximumFractionDigits: digits }).format(number);
}

function calcSoil() {
  const actual = value('soilActual');
  const maximum = value('soilMax');
  const targetField = byId('soilTarget');
  const target = targetField.valueAsNumber;
  const ratio = actual / maximum;
  let message = 'Введите две положительные плотности.';
  if (actual > 0 && maximum > 0 && Number.isFinite(ratio)) {
    message = 'Купл ≈ ' + format(ratio);
    if (target > 0) {
      // Allow binary floating-point error at the equality boundary.
      const tolerance = Number.EPSILON * Math.max(target, ratio);
      message += ratio + tolerance >= target ? ' · порог достигнут' : ' · ниже заданного порога';
    } else if (targetField.value || targetField.validity.badInput) {
      message = 'Введите положительный порог по проекту или оставьте поле пустым.';
    }
  }
  byId('soilResult').textContent = message;
}

function calcSteel() {
  const diameter = value('steelD');
  const quantity = value('steelV');
  const fromLength = byId('steelMode').value === 'length';
  byId('steelVLabel').textContent = fromLength ? 'Длина, м' : 'Масса, т';
  const unitMass = 0.006165 * diameter ** 2;
  const result = fromLength ? quantity * unitMass / 1000 : quantity * 1000 / unitMass;
  const unit = fromLength ? ' т' : ' м';
  byId('steelResult').textContent = quantity >= 0 && Number.isFinite(result)
    ? (fromLength ? 'Масса ≈ ' : 'Длина ≈ ') + format(result, fromLength ? 4 : 2) + unit + ' · ' + format(unitMass) + ' кг/м'
    : 'Введите неотрицательное количество в указанных единицах.';
}

function calcConcrete() {
  const length = value('conL');
  const width = value('conW');
  const thickness = value('conH');
  const reserve = value('conReserve');
  const volume = length * width * thickness;
  const total = volume * (1 + reserve / 100);
  let message = 'Введите положительную длину, ширину и толщину плиты в метрах.';
  if (length > 0 && width > 0 && thickness > 0) {
    message = 'Введите неотрицательный запас. Для расчёта без запаса укажите 0.';
    if (reserve >= 0 && Number.isFinite(total)) {
      message = 'Геометрический объём ≈ ' + format(volume) + ' м³ · с запасом ≈ ' + format(total) + ' м³';
    } else if (reserve >= 0) {
      message = 'Значения слишком велики. Проверьте исходные данные.';
    }
  }
  byId('conResult').textContent = message;
}

function calcPressure() {
  const pressure = value('pressure');
  const converted = pressure / 0.0980665;
  byId('pressureResult').textContent = pressure >= 0 && Number.isFinite(converted)
    ? format(pressure) + ' МПа ≈ ' + format(converted, 2) + ' кгс/см²'
    : 'Введите неотрицательное значение прочности в МПа.';
}

function calcCubes() {
  const volume = value('cubeVolume');
  const step = value('cubeStep');
  const series = value('cubeSeries');
  const count = value('cubeCount');
  const samples = Math.ceil(Number((volume / step).toPrecision(15)));
  const total = samples * series * count;
  const valid = volume > 0 && step > 0 && [series, count, total].every(n => Number.isSafeInteger(n) && n > 0);
  byId('cubeResult').textContent = valid
    ? 'Отборов: ' + samples + ' · Кубов: ' + total
    : 'Введите объём, шаг отбора и целые положительные количества серий и кубов.';
}

const calculators = { calcCubes, calcSoil, calcSteel, calcConcrete, calcPressure };
document.querySelectorAll('.calc').forEach(panel => {
  const field = panel.querySelector('[data-calc]');
  const calculate = calculators[field.dataset.calc];
  panel.addEventListener('input', calculate);
  calculate();
});

const handbook = document.querySelector('.handbook-links');
if (handbook) {
  const links = Array.from(handbook.querySelectorAll('a'));
  const panels = links.map(link => document.querySelector(link.hash));
  function showSection() {
    const active = links.find(link => link.hash === location.hash) || links[0];
    links.forEach((link, index) => {
      const selected = link === active;
      panels[index].hidden = !selected;
      if (selected) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  }
  window.addEventListener('hashchange', showSection);
  showSection();
}

const regionPicker = document.querySelector('.region-picker');
if (regionPicker) {
  document.addEventListener('click', event => {
    if (!regionPicker.contains(event.target)) regionPicker.open = false;
  });
  regionPicker.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      regionPicker.open = false;
      regionPicker.querySelector('summary').focus();
    }
  });
}

if (new URLSearchParams(location.search).get('hero') === 'blue') {
  document.querySelector('.hero')?.classList.add('hero-blue');
}
