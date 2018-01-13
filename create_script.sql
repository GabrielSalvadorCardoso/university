create table universidade.aluno(
id_aluno integer not null,
matricula char(10) not null,
nome varchar(200) not null,
id_curso integer not null,
constraint pk_aluno primary key(id_aluno),
constraint fk_curso_aluno foreign key(id_curso) references universidade.curso(id_curso)
);

create table universidade.curso(
id_curso integer not null,
codigo char(6) not null,
nome varchar(100) not null,
constraint pk_curso primary key(id_curso)
);

create table universidade.disciplina(
id_disciplina integer not null,
codigo char(6) not null,
nome varchar(100) not null,
constraint pk_disciplina primary key(id_disciplina)
);

create table universidade.curso_disciplina(
id_curso_disciplina integer not null,
id_curso integer not null,
id_disciplina integer not null,
constraint pk_curso_disciplina primary key(id_curso_disciplina),
constraint fk_curso_curso_disciplina foreign key(id_curso) references universidade.curso(id_curso),
constraint fk_disciplina_curso_disciplina foreign key(id_disciplina) references universidade.disciplina(id_disciplina)
);

insert into universidade.aluno (id_aluno, matricula, nome, id_curso) values
(1, '2015100001', 'Gabriel Cardoso', 1),
(2, '2015100002', 'Jõao Bastos', 2),
(3, '2015100003', 'Carlos Andrade', 3),
(4, '2015100004', 'Luiz Moraiz', 4),
(5, '2015100005', 'Camila Gonzales', 5),
(6, '2015100006', 'Marcos Borges', 1),
(7, '2015100007', 'Mario Andrade', 2),
(8, '2015100008', 'Maria Gouveia', 3),
(9, '2015100009', 'Joana Bastos', 4),
(10, '2015100010', 'Ana Diaz', 5),
(11, '2015100011', 'Fabio Moraiz', 1),
(12, '2015100012', 'André Nunez', 2),
(13, '2015100013', 'Antônia Marques', 3),
(14, '2015100014', 'Douglas Costa', 4),
(15, '2015100015', 'Denis Batista', 5);

insert into universidade.curso (id_curso, codigo, nome) values
(1, 'CCO001', 'Ciência da Computação'),
(2, 'ADM001', 'Administração'),
(3, 'ADS001', 'Análise e Desenvolvimento de Sistemas'),
(4, 'DSG001', 'Design'),
(5, 'ENG001', 'Engenharia Civil');

insert into universidade.disciplina (id_disciplina, codigo, nome) values
(1, '111001', 'Programação I'),
(2, '222001', 'Conceitos de Gestão'),
(3, '333001', 'Matemática Discreta'),
(4, '444001', 'Design de Interfaces'),
(5, '555001', 'Programação II'),
(6, '666001', 'Gestão de RH'),
(7, '777001', 'Ética e Responsabilidade Social'),
(8, '888001', 'Banco de Dados I'),
(9, '999001', 'História do Design'),
(10, '000001', 'Estatistica');

insert into universidade.curso_disciplina (id_curso_disciplina, id_curso, id_disciplina) values
(1, 1, 1),
(2, 1, 2),
(3, 1, 3),
(4, 1, 5),
(5, 1, 7),
(6, 1, 8),
(7, 1, 10),
(8, 2, 2),
(9, 2, 6),
(10, 2, 7),
(11, 3, 1),
(12, 3, 2),
(13, 3, 3),
(14, 3, 5),
(15, 3, 7),
(16, 3, 8),
(18, 3, 10),
(19, 4, 2),
(20, 4, 4),
(21, 4, 7),
(22, 4, 9),
(23, 5, 2),
(24, 5, 3),
(25, 5, 7),
(26, 5, 10);

select * from universidade.aluno;
select * from universidade.curso;
select * from universidade.disciplina;
select * from universidade.curso_disciplina;

create sequence
universidade.aluno_id_seq
increment by 1
minvalue 1
start 16;

alter table
universidade.aluno
alter column id_aluno
set default nextval('universidade.aluno_id_seq');


create sequence universidade.curso_id_seq increment by 1 minvalue 1 start 6;
alter table universidade.curso alter column id_curso set default nextval('universidade.curso_id_seq');

create sequence universidade.disciplina_id_seq increment by 1 minvalue 1 start 11;
alter table universidade.disciplina alter column id_disciplina set default nextval('universidade.disciplina_id_seq');

create sequence universidade.curso_disciplina_id_seq increment by 1 minvalue 1 start 27;
alter table universidade.curso_disciplina alter column id_curso_disciplina set default nextval('universidade.curso_disciplina_id_seq');
