-- Estrutura compatível com as consultas presentes em tcc_api/main.py
-- e tcc_api/importar_resultados_ansys.py.
-- Executar com usuário MySQL administrador. NUNCA adicionar senhas ao GitHub.
CREATE DATABASE IF NOT EXISTS tcc_viga
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tcc_viga;

CREATE TABLE IF NOT EXISTS materiais (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL UNIQUE,
  modulo_elasticidade_gpa DECIMAL(12,4) NULL,
  coeficiente_poisson DECIMAL(8,5) NULL,
  densidade_kg_m3 DECIMAL(12,3) NULL,
  limite_escoamento_mpa DECIMAL(12,4) NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vigas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  material_id INT NOT NULL,
  nome VARCHAR(200) NOT NULL,
  comprimento_mm DECIMAL(14,2) NOT NULL,
  largura_mm DECIMAL(14,2) NOT NULL,
  altura_mm DECIMAL(14,2) NOT NULL,
  UNIQUE KEY uq_viga_nome_material (nome, material_id),
  CONSTRAINT fk_viga_material FOREIGN KEY (material_id) REFERENCES materiais(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS simulacoes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  viga_id INT NOT NULL,
  nome VARCHAR(200) NOT NULL,
  tamanho_malha_mm DECIMAL(10,2) NOT NULL,
  descricao_carregamento TEXT NULL,
  condicoes_contorno TEXT NULL,
  origem_dados VARCHAR(20) NOT NULL,
  UNIQUE KEY uq_viga_malha_origem (viga_id, tamanho_malha_mm, origem_dados),
  CONSTRAINT fk_simulacao_viga FOREIGN KEY (viga_id) REFERENCES vigas(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resultados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  simulacao_id INT NOT NULL UNIQUE,
  tensao_von_mises_max_mpa DECIMAL(18,6) NOT NULL,
  deslocamento_total_max_mm DECIMAL(18,6) NOT NULL,
  deslocamento_y_min_mm DECIMAL(18,6) NOT NULL,
  deslocamento_y_max_mm DECIMAL(18,6) NOT NULL,
  fator_seguranca_min DECIMAL(18,6) NOT NULL,
  CONSTRAINT fk_resultado_simulacao FOREIGN KEY (simulacao_id) REFERENCES simulacoes(id)
) ENGINE=InnoDB;

INSERT INTO materiais (nome, modulo_elasticidade_gpa, coeficiente_poisson,
                       densidade_kg_m3, limite_escoamento_mpa)
VALUES ('ASTM A36', 200.0000, 0.26000, 7850.000, 250.0000)
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

INSERT INTO vigas (material_id, nome, comprimento_mm, largura_mm, altura_mm)
SELECT m.id, 'Viga retangular 3000 x 50 x 150 mm', 3000.00, 50.00, 150.00
FROM materiais m WHERE m.nome = 'ASTM A36'
ON DUPLICATE KEY UPDATE nome = VALUES(nome);
