class Cell() {
  public:
    Cell *up;
    Cell *down;
    Cell *left;
    Cell *right;
    Cell *header = NULL;
    std::pair<int, unsigned int> *indexes;

    Cell() {
        this->up = &this;
        this->down = &this;
        this->left = &this;
        this->right = &this;
    }
}

class HeaderCell(Cell) {
  public:
    std::string name;
    unsigned int size;
    bool primary;
    bool is_first;

    HeaderCell(std::string name, bool primary) {
        this->name = name;
        this->size = 0;
        this->primary = primary;
        this->is_first = false;
    }
}

class RainAlgorithmX() {
  private:
    std::pair<int, int> pos;
    int seed;

    int num_rows = 0;
    int num_columns = 0;
    std::vector<HeaderCell> column_list;

    std::vector<??> row_headers;
    std::vector<??> solution_rows;  // List of row cells
    std::map<int, std::frozen_set<??>> bad_solutions;


  public:
    RainAlgorithmX(std::vector<std::pair<std::string, bool>> column_headers, 
                   std::vector<??> row_headers, std::vector<std::vector<int>> rows,
                   std::pair<int, int> pos, int seed) {
        this->pos = pos;
        this->seed = seed;

        this->header = HeaderCell("<H>", true);
        this->header->is_first = true;

        // Add columns
        HeaderCell *previous = this->header;
        HeaderCell cell;
        // Link every column together
        for(unsigned int i = 0; i < column_headers.count(); i++) {
            std::string name = column_headers[i].first;
            bool primary = column_headers[i].second;
            cell = HeaderCell(name, primary);
            cell->indexes = make_pair(-1, this->num_columns);

            this->column_list.push_back(cell);
            if (primary) {
                previous->right = &cell;
                cell->left = &previous;
                previous = &cell;
            }
            this->num_columns++;
        }

        previous->right = &this->header;
        this->header.left = &previous;

        // Add rows
        this->row_headers = row_headers;

        Cell start;
        for(unsigned int i = 0; i < rows.count(); i++) {
            previous = NULL;
            start = NULL;
            cell = NULL;

            for (unsigned int j; j < rows[i].count(); j++) {
                int idx = rows[i][j];
                cell = Cell();
                cell.indexes = make_pair(this->num_rows, idx);

                if (previous != NULL) {
                    previous->right = &cell;
                    cell->left = &previous;
                } else {
                    start = cell;
                }

                HeaderCell column_header_cell = this->column_list[idx];
                // Link the cell with the previous one and with the correct column cell
                Cell last = column_header_cell->up;
                last->down = &cell;
                cell->up = &last;
                column_header_cell->up = &cell;
                cell->down = &column_header_cell;
                cell->header = &column_header_cell;
                column_header_cell->size++;
                previous = &cell;
            }

            start->left = &cell;
            cell->right = &start;
            this->num_rows++;
        }
    }
}