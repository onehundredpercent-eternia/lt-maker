const unsigned int LIMIT = 10000;

class HeaderCell; // Necessary so Cell knows what a header cell is on compilation

class Cell() {
  public:
    Cell *up;
    Cell *down;
    Cell *left;
    Cell *right;
    HeaderCell *header = NULL;
    int row;
    unsigned int col;

    Cell() {
        this->up = this;
        this->down = this;
        this->left = this;
        this->right =this;
    }
}

class HeaderCell : public Cell {
  public:
    HeaderCell* left;
    HeaderCell* right;
    
    std::string name;
    size_t size = 0;
    bool primary; // Whether this column must be included in the solution
    bool is_first = false;

    HeaderCell(std::string name, bool primary) : Cell() {
        super().Cell();
        this->name = name;
        this->primary = primary;
    }
}

typedef std::unordered_set<Cell*> cell_set;

class RainAlgorithmX() {
  private:
    Pos pos;
    int seed;

    int num_rows = 0;
    int num_columns = 0;

    HeaderCell* header;

    std::vector<std::string> row_headers;
    std::vector<Cell*> solution_rows;  // List of row cells
    std::unordered_map<unsigned int, cell_set> bad_solutions = {}; // Key: Depth, Value: Set of row cells

    // Column header is string + bool
    // String is name of column
    // bool is whether this column must be included in the solution
  public:
    RainAlgorithmX(std::vector<std::pair<std::string, bool>> column_headers, 
                   std::vector<std::string> row_headers, 
                   std::vector<std::vector<int>> rows,
                   const int seed) {
        this->seed = seed;
        std::vector<HeaderCell> column_list;

        this->header = new HeaderCell("<H>", true);
        this->header->is_first = true;

        // Add columns
        HeaderCell* previous_header_cell = this->header;
        HeaderCell* header_cell;
        // Link every column together
        for(size_t i = 0; i < column_headers.size(); i++) {
            std::string name = column_headers[i].first;
            bool primary = column_headers[i].second;
            header_cell = new HeaderCell(name, primary);
            header_cell->row = -1;
            header_cell->col = this->num_columns;

            column_list.push_back(header_cell);
            if (primary) {
                previous_header_cell->right = header_cell;
                header_cell->left = previous_header_cell;
                previous_header_cell = header_cell;
            }
            this->num_columns++;
        }

        // At the end of the column, link back to the start of the column (the H cell)
        previous_header_cell->right = this->header;
        this->header->left = previous_header_cell;

        // Add rows
        this->row_headers = row_headers;

        Cell *start, *last;
        HeaderCell* column_header_cell;
        for(size_t i = 0; i < rows.size(); i++) {
            previous = NULL;
            start = NULL;
            cell = NULL;

            for (size_t j = 0; j < rows[i].size(); j++) {
                int idx = rows[i][j];  // index of a valid option
                cell = new Cell();
                cell->row = this->num_rows;
                cell->col = idx;

                if (previous != NULL) {
                    previous->right = cell;
                    cell->left = previous;
                } else {
                    start = cell;
                }

                column_header_cell = column_list[idx];
                // Link the cell with the previous one and with the correct column cell
                last = column_header_cell->up;
                last->down = cell;
                cell->up = last;
                column_header_cell->up = cell;
                cell->down = column_header_cell;
                cell->header = column_header_cell;
                column_header_cell->size++;
                previous = cell;
            }
            // At the end of the row, link back to the start of the row
            start->left = cell;
            cell->right = start;
            this->num_rows++;
        }
    }

    std::vector<std::string> get_solution() { 
        std::vector<std::string> solution;
        for (size_t i = 0; i < this.solution_rows->size(); i++) {
            solution.push_back(this->row_headers[self->solution_rows[i]->indexes[0]])
        }
        std::sort(solution.begin(), solution.end());
        return solution;
    }

    HeaderCell* get_minimum_column() {
        /**
        Finds the column with the minimum size.
        Returns its index.

        Runs rightward through each column finding the header cell with the smallest size
         */
        if (this->header->right->is_first) {
            throw EmptyMatrixException();
        }
        HeaderCell *h = this->header;
        HeaderCell *minimum_column = this->header->right;
        h = h->right->right;
        do {
            if (!h->is_first && h->size < minimum_column->size) {
                minimum_column = h;
            }
            h = h->right;
        } while (h != this->header);

        return minimum_column;
    }

    bool solve() {
        /**
        Attempts to solve the exact cover problem and returns whether it has done so. 
        */
        unsigned int counter = 0;
        while (counter < LIMIT) {
            counter++;
            if (this->header->right == this->header) {
                // solution is found when there is only one column
                return true;
            }
            bool output = this->process();
            if (!output) {
                // No valid solutions at all
                return false;
            }
        }
        std::cout<<"Infinite Loop Detected!"<<std::endl;
        return false;
    }

    unsigned int subsolve() {
        /**
         Does a single processing step:
         0 - There are no valid solutions at all
         1 - Not complete
         2 - A solution was found
         */
        if (this->header->right == this->header) {
            // solution is found when there is only one column
            return 2;
        }
        bool output = this->process();
        if (!output) {
            return 0;
        }
        return 1;
    }

    bool revert() {
        /** 
        Call when the processing is unable to find any solutions at this level 
        */
        size_t depth = this->solution_rows.size();
        if (this->bad_solutions.count(depth) > 0) {
            this->bad_solutions[depth].clear();
        }

        if (this->solution_rows.size() > 0) {
            Cell* bad_row_cell = this->solution_rows.back();
            this->solution_rows.pop_back();
            // Uncover the bad row cell since we are reverting ever using it
            Cell* left_cell;
            for (left_cell = bad_row_cell->left; left_cell != bad_row_cell; left_cell = left_cell->left) {
                this->uncover(left_cell->header);
            }
            this->uncover(bad_row_cell->header);
            // But make sure we remember that we did use it here so we don't try again
            if (this->bad_solutions.count(depth - 1) == 0) {
                this->bad_solutions[depth - 1] = cell_set();
            }
            this->bad_solutions[depth - 1].insert(bad_row_cell);
            return true;
        } else {
            return false; // No valid solutions at all
        }
    }

    bool process() {
        Cell *right_cell, *down_cell;
        HeaderCell* column_header_cell = this->get_minimum_column();

        if (column_header_cell->size == 0) {
            return this->revert();
        }

        int depth = this->solution_rows.size();
        cell_set bad_row_cells;
        // check whether the depth exists in the bad solution map
        if (this->bad_solutions.find(depth) != this->bad_solutions.end()) {
            bad_row_cells = this->bad_solutions.at(depth);
        } else {
            bad_row_cells = cell_set();
        }

        std::vector<Cell*> possible_rows;

        for (down_cell = column_header_cell->down; down_cell != column_header_cell; down_cell = down_cell->down) {
            if (bad_row_cells.count(down_cell) == 0) {
                possible_rows.push_back(down_cell)
            }
        }

        if (possible_rows.size() == 0) {
            return this->revert();
        }

        Cell* row_cell = random_choice(possible_rows, this->pos, this->seed);

        this->solution_rows.push_back(row_cell);

        cover(column_header_cell);
        for (right_cell = row_cell->right; right_cell != row_cell; right_cell = right_cell->right) {
            cover(right_cell->header);
        }
        return true;
    }

    void cover(HeaderCell* column_header_cell) {
        /**
        Cover the given node completely
        */
        // unlink column header from it's neighbors
        column_header_cell->left->right = column_header_cell->right;
        column_header_cell->right->left = column_header_cell->left;

        Cell *row_cell, *right_cell;
        // Move down the column and remove each row by traversing right
        for (row_cell = column_header_cell->down; row_cell != column_header_cell; row_cell = row_cell->down) {
            for(right_cell = row_cell->right; right_cell != row_cell; right_cell = right_cell->right) {
                right_cell->up->down = right_cell->down;
                right_cell->down->up = right_cell->up;

                // After unlinking, decrement the size in the column header
                right_cell->header->size -= 1;
            }
        }
    }

    void uncover(HeaderCell* column_header_cell) {
        /**
        Uncover the given cell completely
         */

        Cell *row_cell, *left_cell;
        // Move up the column and link back each row by traversing left
        for (row_cell = column_header_cell->up; row_cell != column_header_cell; row_cell = row_cell->up) {
            for(left_cell = row_cell->left; left_cell != row_cell; left_cell = left_cell->left) {
                left_cell->up->down = left_cell;
                left_cell->down->up = left_cell;

                // After unlinking, decrement the size in the column header
                left_cell->header->size += 1;
            }
        }

        // Link the column header to its neighbours
        column_header_cell->left->right = column_header_cell;
        column_header_cell->right->left = column_header_cell;
    }
}

// Driver code
int main() {
    /**
      A B C D E
    0   X X   X
    1 X X   X
    2 X
    3 X X X X X

    Try to cover each column with a set of rows, but you can't duplicate covering a column with two rows
    Answer should be row3 or (row0, row2) or (row0, row1)
    
     */
    std::vector<std::pair<std::string, bool>> columns;
    columns.push_back(std::make_pair<std::string, bool>("a", true));
    columns.push_back(std::make_pair<std::string, bool>("b", true));
    columns.push_back(std::make_pair<std::string, bool>("c", true));
    columns.push_back(std::make_pair<std::string, bool>("d", false));
    columns.push_back(std::make_pair<std::string, bool>("e", true));

    std::vector<std::vector<int>> rows;
    rows.push_back(new std::vector<int>(1, 2, 4));
    rows.push_back(new std::vector<int>(0, 1, 3));
    rows.push_back(new std::vector<int>(0));
    rows.push_back(new std::vector<int>(0, 1, 2, 3, 4));

    std::vector<std::string> row_names = new std::vector<std::string>("row0", "row1", "row2", "row3");

    auto d = RainAlgorithmX(columns, row_names, rows, std::make_pair<int, int>(0, 0), 1);
    bool output = d.solve();
    if (output) {
        std::cout<<d.get_solution()<<std::endl;
    } else {
        std::cout<<"No valid solution"<<std::endl;
    }
}